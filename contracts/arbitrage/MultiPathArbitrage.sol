// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IERC20.sol";
import "../interfaces/IMultiPathArbitrage.sol";
import "../interfaces/IUniswapV3Router.sol";
import "../interfaces/IUniswapV3Factory.sol";
import "../interfaces/IUniswapV3Pool.sol";

contract MultiPathArbitrage is IMultiPathArbitrage, Ownable {
    // Constants
    uint256 private constant BASIS_POINTS = 10000;
    uint256 private constant EMERGENCY_WITHDRAWAL_DELAY = 24 hours;

    // Configuration
    uint256 public minProfitBasisPoints;
    uint256 public maxTradeSize;
    uint256 public emergencyWithdrawalDelay;
    uint256 public maxGasPrice;
    bool public usePrivateMempool;
    address public flashbotsRelayer;

    // Registries
    address public priceFeedRegistry;
    address public dexRegistry;

    // Emergency withdrawal
    uint256 public emergencyWithdrawalTimestamp;

    // Events
    event ArbitrageExecuted(
        address[] path,
        address[] dexes,
        uint256 amountIn,
        uint256 amountOut,
        uint256 profit
    );

    event EmergencyWithdrawalRequested(uint256 timestamp);
    event EmergencyWithdrawalExecuted(address token, uint256 amount);

    // Errors
    error InsufficientProfit();
    error ExcessiveTradeSize();
    error ExcessiveGasPrice();
    error InvalidPath();
    error SwapFailed();
    error WithdrawalDelayNotMet();

    constructor(
        uint256 _minProfitBasisPoints,
        uint256 _maxTradeSize,
        uint256 _emergencyWithdrawalDelay
    ) {
        minProfitBasisPoints = _minProfitBasisPoints;
        maxTradeSize = _maxTradeSize;
        emergencyWithdrawalDelay = _emergencyWithdrawalDelay;
    }

    // @CRITICAL: Execute multi-path arbitrage
    function executeMultiPathArbitrage(
        ArbitragePath calldata path,
        uint256 amount
    ) external override returns (bool) {
        // Validate path
        if (path.steps.length == 0) revert InvalidPath();
        if (amount > maxTradeSize) revert ExcessiveTradeSize();
        if (tx.gasprice > maxGasPrice) revert ExcessiveGasPrice();

        // Transfer initial tokens
        address firstToken = path.steps[0].path[0];
        IERC20(firstToken).transferFrom(msg.sender, address(this), amount);

        // Track initial balance
        uint256 startBalance = IERC20(firstToken).balanceOf(address(this));

        // Execute each step
        uint256 currentAmount = amount;
        for (uint256 i = 0; i < path.steps.length; i++) {
            PathStep memory step = path.steps[i];

            // Approve router
            IERC20(step.path[0]).approve(step.dex, currentAmount);

            // Execute swap
            try this._executeV3Swap(
                step.dex,
                step.path[0],
                step.path[1],
                currentAmount,
                step.minOutput
            ) returns (uint256 amountOut) {
                currentAmount = amountOut;
            } catch {
                revert SwapFailed();
            }

            // Clear approval
            IERC20(step.path[0]).approve(step.dex, 0);
        }

        // Verify profit
        uint256 endBalance = IERC20(firstToken).balanceOf(address(this));
        uint256 profit = endBalance - startBalance;
        uint256 minProfit = (amount * minProfitBasisPoints) / BASIS_POINTS;

        if (profit < minProfit) revert InsufficientProfit();

        // Transfer profit back
        IERC20(firstToken).transfer(msg.sender, endBalance);

        // Emit event
        address[] memory pathTokens = new address[](path.steps.length + 1);
        address[] memory dexes = new address[](path.steps.length);

        for (uint256 i = 0; i < path.steps.length; i++) {
            pathTokens[i] = path.steps[i].path[0];
            dexes[i] = path.steps[i].dex;
        }
        pathTokens[path.steps.length] = path.steps[path.steps.length - 1].path[1];

        emit ArbitrageExecuted(
            pathTokens,
            dexes,
            amount,
            endBalance,
            profit
        );

        return true;
    }

    // @CRITICAL: Execute V3 swap
    function _executeV3Swap(
        address router,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut
    ) external returns (uint256) {
        // Find best fee tier
        uint24[] memory feeTiers = new uint24[](3);
        feeTiers[0] = 500;   // 0.05%
        feeTiers[1] = 3000;  // 0.3%
        feeTiers[2] = 10000; // 1%

        uint24 bestFeeTier = feeTiers[0];
        uint256 bestOutput = 0;

        IUniswapV3Router v3Router = IUniswapV3Router(router);
        address factory = v3Router.factory();

        // Check each fee tier
        for (uint256 i = 0; i < feeTiers.length; i++) {
            address pool = IUniswapV3Factory(factory).getPool(tokenIn, tokenOut, feeTiers[i]);
            if (pool == address(0)) continue;

            IUniswapV3Pool poolContract = IUniswapV3Pool(pool);
            if (poolContract.liquidity() == 0) continue;

            // Try this fee tier
            try v3Router.exactInputSingle(
                IUniswapV3Router.ExactInputSingleParams({
                    tokenIn: tokenIn,
                    tokenOut: tokenOut,
                    fee: feeTiers[i],
                    recipient: address(this),
                    deadline: block.timestamp,
                    amountIn: amountIn,
                    amountOutMinimum: minAmountOut,
                    sqrtPriceLimitX96: 0
                })
            ) returns (uint256 output) {
                if (output > bestOutput) {
                    bestOutput = output;
                    bestFeeTier = feeTiers[i];
                }
            } catch {
                continue;
            }
        }

        if (bestOutput == 0) revert SwapFailed();

        // Execute swap with best fee tier
        return v3Router.exactInputSingle(
            IUniswapV3Router.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: bestFeeTier,
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountIn,
                amountOutMinimum: minAmountOut,
                sqrtPriceLimitX96: 0
            })
        );
    }

    // @CRITICAL: Set registries
    function setRegistries(
        address _priceFeedRegistry,
        address _dexRegistry
    ) external onlyOwner {
        priceFeedRegistry = _priceFeedRegistry;
        dexRegistry = _dexRegistry;
    }

    // @CRITICAL: Set MEV protection parameters
    function setMEVProtection(
        address _flashbotsRelayer,
        bool _usePrivateMempool,
        uint256 _maxGasPrice
    ) external onlyOwner {
        flashbotsRelayer = _flashbotsRelayer;
        usePrivateMempool = _usePrivateMempool;
        maxGasPrice = _maxGasPrice;
    }

    // @CRITICAL: Request emergency withdrawal
    function requestEmergencyWithdrawal() external onlyOwner {
        emergencyWithdrawalTimestamp = block.timestamp + emergencyWithdrawalDelay;
        emit EmergencyWithdrawalRequested(emergencyWithdrawalTimestamp);
    }

    // @CRITICAL: Execute emergency withdrawal
    function executeEmergencyWithdrawal(
        address token
    ) external onlyOwner {
        if (block.timestamp < emergencyWithdrawalTimestamp) {
            revert WithdrawalDelayNotMet();
        }

        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).transfer(owner(), balance);
            emit EmergencyWithdrawalExecuted(token, balance);
        }
    }
}
