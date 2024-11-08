// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../MultiPathArbitrage.sol";
import "../FlashLoanManager.sol";

contract ExecutionComponentsFactory is Ownable {
    // Events
    event ComponentsDeployed(
        address arbitrageBot,
        address flashLoanManager
    );

    // Deploy execution components
    function deployExecutionComponents(
        address priceFeedRegistry,
        address dexRegistry,
        address aaveAddressProvider,
        uint256 defaultMinProfitBasisPoints,
        uint256 defaultMaxTradeSize,
        uint256 emergencyWithdrawalDelay
    ) external returns (
        address arbitrageBot,
        address flashLoanManager
    ) {
        // Deploy arbitrage bot
        MultiPathArbitrage arbitrageBotContract = new MultiPathArbitrage(
            defaultMinProfitBasisPoints,
            defaultMaxTradeSize,
            emergencyWithdrawalDelay
        );

        // Set registries
        arbitrageBotContract.setRegistries(
            priceFeedRegistry,
            dexRegistry
        );

        // Deploy flash loan manager with arbitrage bot address
        FlashLoanManager flashLoanManagerContract = new FlashLoanManager(
            address(arbitrageBotContract)
        );

        emit ComponentsDeployed(
            address(arbitrageBotContract),
            address(flashLoanManagerContract)
        );

        return (
            address(arbitrageBotContract),
            address(flashLoanManagerContract)
        );
    }
}
