// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./interfaces/IERC20.sol";
import "./dex/PriceFeedRegistry.sol";
import "./dex/DEXRegistry.sol";
import "./interfaces/dex/IUniswapInterfaces.sol";

contract ArbitrageBot {
    uint256 private immutable DEADLINE_EXTENSION = 15 minutes;
    uint256 private immutable BASIS_POINTS = 10000;

    PriceFeedRegistry public immutable priceFeedRegistry;
    DEXRegistry public immutable dexRegistry;

    address public owner;
    bool public paused;

    struct TradingParams {
        uint96 defaultMinProfitBasisPoints;
        uint96 defaultMaxTradeSize;
        uint64 emergencyWithdrawalDelay;
    }
    TradingParams public tradingParams;

    struct EmergencyState {
        uint64 lastEmergencyWithdrawalRequest;
        bool emergencyWithdrawalRequested;
    }
    EmergencyState public emergencyState;

    event TradeExecuted(
        address indexed tokenIn,
        address indexed tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        address dex,
        uint256 priceAtExecution
    );
    event EmergencyWithdrawalRequested(uint256 timestamp);
    event EmergencyWithdrawalCancelled();
    event ParametersUpdated(
        uint96 defaultMinProfitBasisPoints,
        uint96 defaultMaxTradeSize,
        uint64 emergencyWithdrawalDelay
    );

    error InvalidParameters();
    error InsufficientProfit();
    error ExcessiveSlippage();
    error StalePrice();
    error InvalidPrice();
    error WithdrawalDelayNotMet();
    error EmergencyWithdrawalNotRequested();
    error OnlyOwner();
    error ContractPaused();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert ContractPaused();
        _;
    }

    constructor(
        uint96 _defaultMinProfitBasisPoints,
        uint96 _defaultMaxTradeSize,
        uint64 _emergencyWithdrawalDelay,
        address _priceFeedRegistry,
        address _dexRegistry
    ) {
        if (_defaultMinProfitBasisPoints == 0 || _defaultMaxTradeSize == 0 || _emergencyWithdrawalDelay == 0)
            revert InvalidParameters();

        tradingParams = TradingParams({
            defaultMinProfitBasisPoints: _defaultMinProfitBasisPoints,
            defaultMaxTradeSize: _defaultMaxTradeSize,
            emergencyWithdrawalDelay: _emergencyWithdrawalDelay
        });

        priceFeedRegistry = PriceFeedRegistry(_priceFeedRegistry);
        dexRegistry = DEXRegistry(_dexRegistry);
        owner = msg.sender;
    }

    function executeTrade(
        address dex,
        uint256 amountIn,
        uint256 amountOutMin,
        address[] calldata path
    )
        external
        onlyOwner
        whenNotPaused
    {
        address tokenIn = path[0];
        address tokenOut = path[path.length - 1];

        dexRegistry.validateTrade(dex, tokenIn, tokenOut);

        (uint256 chainlinkPrice, uint8 decimals) = priceFeedRegistry.getPrice(
            tokenIn,
            tokenOut
        );

        IUniswapV2Router router = IUniswapV2Router(dex);

        uint256[] memory amounts = router.getAmountsOut(amountIn, path);
        uint256 expectedOut = amounts[amounts.length - 1];

        uint256 dexPrice;
        unchecked {
            dexPrice = (expectedOut * (10**decimals)) / amountIn;
        }

        uint256 minProfit;
        unchecked {
            minProfit = (chainlinkPrice * tradingParams.defaultMinProfitBasisPoints) / BASIS_POINTS;
        }
        if (dexPrice <= chainlinkPrice + minProfit)
            revert InsufficientProfit();

        IERC20 token = IERC20(tokenIn);
        if (token.allowance(address(this), dex) < amountIn) {
            require(token.approve(dex, type(uint256).max), "Approval failed");
        }

        uint256[] memory result = router.swapExactTokensForTokens(
            amountIn,
            amountOutMin,
            path,
            address(this),
            block.timestamp + DEADLINE_EXTENSION
        );

        emit TradeExecuted(
            tokenIn,
            tokenOut,
            amountIn,
            result[result.length - 1],
            dex,
            chainlinkPrice
        );
    }

    function updateParameters(
        uint96 _defaultMinProfitBasisPoints,
        uint96 _defaultMaxTradeSize,
        uint64 _emergencyWithdrawalDelay
    ) external onlyOwner {
        if (_defaultMinProfitBasisPoints == 0 || _defaultMaxTradeSize == 0 || _emergencyWithdrawalDelay == 0)
            revert InvalidParameters();

        tradingParams = TradingParams({
            defaultMinProfitBasisPoints: _defaultMinProfitBasisPoints,
            defaultMaxTradeSize: _defaultMaxTradeSize,
            emergencyWithdrawalDelay: _emergencyWithdrawalDelay
        });

        emit ParametersUpdated(
            _defaultMinProfitBasisPoints,
            _defaultMaxTradeSize,
            _emergencyWithdrawalDelay
        );
    }

    function pause() external onlyOwner {
        paused = true;
    }

    function unpause() external onlyOwner {
        paused = false;
    }

    function requestEmergencyWithdrawal() external onlyOwner {
        emergencyState.emergencyWithdrawalRequested = true;
        emergencyState.lastEmergencyWithdrawalRequest = uint64(block.timestamp);
        emit EmergencyWithdrawalRequested(block.timestamp);
    }

    function cancelEmergencyWithdrawal() external onlyOwner {
        emergencyState.emergencyWithdrawalRequested = false;
        emit EmergencyWithdrawalCancelled();
    }

    function executeEmergencyWithdrawal(
        address[] calldata tokens
    ) external onlyOwner {
        if (!emergencyState.emergencyWithdrawalRequested)
            revert EmergencyWithdrawalNotRequested();

        if (block.timestamp < emergencyState.lastEmergencyWithdrawalRequest + tradingParams.emergencyWithdrawalDelay)
            revert WithdrawalDelayNotMet();

        address ownerAddr = owner;
        uint256 length = tokens.length;

        unchecked {
            for (uint256 i = 0; i < length; ++i) {
                address token = tokens[i];
                IERC20 tokenContract = IERC20(token);
                uint256 balance = tokenContract.balanceOf(address(this));
                if (balance > 0) {
                    require(tokenContract.transfer(ownerAddr, balance), "Transfer failed");
                }
            }
        }

        emergencyState.emergencyWithdrawalRequested = false;
    }

    function simulateTrade(
        address dex,
        uint256 amountIn,
        address[] calldata path
    ) external view returns (
        uint256[] memory expectedAmounts,
        uint256 chainlinkPrice,
        uint8 priceDecimals
    ) {
        address tokenIn = path[0];
        address tokenOut = path[path.length - 1];

        dexRegistry.validateTrade(dex, tokenIn, tokenOut);

        (chainlinkPrice, priceDecimals) = priceFeedRegistry.getPrice(
            tokenIn,
            tokenOut
        );

        expectedAmounts = IUniswapV2Router(dex).getAmountsOut(amountIn, path);
    }

    function getTokenBalance(
        address token
    ) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }
}
