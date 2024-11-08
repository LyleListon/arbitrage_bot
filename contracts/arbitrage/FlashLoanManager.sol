// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "../interfaces/IERC20.sol";
import "../interfaces/IMultiPathArbitrage.sol";

// @CRITICAL: Manages flash loan operations for arbitrage
contract FlashLoanManager {
    // Constants
    uint256 private constant BASIS_POINTS = 10000;
    uint256 private constant FLASH_LOAN_FEE = 9; // 0.09%

    // Contracts
    IMultiPathArbitrage public arbitrageBot;

    // Events
    event FlashLoanExecuted(
        address indexed token,
        uint256 amount,
        uint256 fee,
        uint256 profit
    );

    event FlashLoanFailed(
        address indexed token,
        uint256 amount,
        string reason
    );

    // Errors
    error InsufficientProfit(uint256 profit, uint256 required);
    error UnauthorizedCallback();
    error ExecutionFailed(string reason);

    constructor(address _arbitrageBot) {
        arbitrageBot = IMultiPathArbitrage(_arbitrageBot);
    }

    // @CRITICAL: Execute arbitrage with flash loan
    function executeWithFlashLoan(
        address token,
        uint256 amount,
        FlashLoanParams calldata params
    ) external {
        // Calculate flash loan fee
        uint256 fee = (amount * FLASH_LOAN_FEE) / BASIS_POINTS;

        // Verify minimum profit covers fee
        if (params.minProfit <= fee) {
            revert InsufficientProfit(params.minProfit, fee);
        }

        // Simplified flash loan logic (replace with actual implementation)
        IERC20(token).transferFrom(msg.sender, address(this), amount);

        bool success = _executeArbitrage(token, amount, params);

        if (!success) {
            IERC20(token).transfer(msg.sender, amount);
            revert ExecutionFailed("Arbitrage execution failed");
        }

        // Transfer profit back to user
        uint256 balance = IERC20(token).balanceOf(address(this));
        uint256 profit = balance > amount + fee ? balance - amount - fee : 0;
        IERC20(token).transfer(msg.sender, amount + profit);

        emit FlashLoanExecuted(token, amount, fee, profit);
    }

    function _executeArbitrage(
        address token,
        uint256 amount,
        FlashLoanParams memory params
    ) private returns (bool) {
        try arbitrageBot.executeMultiPathArbitrage(
            IMultiPathArbitrage.ArbitragePath({
                steps: _convertToPathSteps(params),
                totalGasEstimate: 0,
                expectedProfit: params.minProfit,
                useFlashLoan: true
            }),
            amount
        ) {
            return true;
        } catch Error(string memory reason) {
            emit FlashLoanFailed(token, amount, reason);
            return false;
        } catch {
            emit FlashLoanFailed(token, amount, "Unknown error");
            return false;
        }
    }

    // Convert flash loan params to path steps
    function _convertToPathSteps(
        FlashLoanParams memory params
    ) private pure returns (IMultiPathArbitrage.PathStep[] memory) {
        IMultiPathArbitrage.PathStep[] memory steps = new IMultiPathArbitrage.PathStep[](params.dexes.length);

        for (uint256 i = 0; i < params.dexes.length; i++) {
            address[] memory path = new address[](2);
            path[0] = params.tokens[i];
            path[1] = params.tokens[i + 1];

            steps[i] = IMultiPathArbitrage.PathStep({
                dex: params.dexes[i],
                path: path,
                expectedOutput: 0,
                minOutput: 0,
                gasEstimate: 0
            });
        }

        return steps;
    }

    // Struct for flash loan parameters
    struct FlashLoanParams {
        address[] tokens;
        address[] dexes;
        uint256 amount;
        uint256 minProfit;
    }
}
