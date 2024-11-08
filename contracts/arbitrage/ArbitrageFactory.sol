// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IArbitrageComponents.sol";
import {PriceFeedRegistry} from "../dex/PriceFeedRegistry.sol";
import {DEXRegistry} from "../dex/DEXRegistry.sol";
import {RegistryFactory as RegistryFactoryImpl} from "./factories/RegistryFactory.sol";
import {CoreComponentsFactory as CoreComponentsFactoryImpl} from "./factories/CoreComponentsFactory.sol";
import {ExecutionComponentsFactory as ExecutionComponentsFactoryImpl} from "./factories/ExecutionComponentsFactory.sol";

// @CRITICAL: Factory for deploying and managing arbitrage components
contract ArbitrageFactory is Ownable {
    // Deployed contracts
    IMultiPathArbitrage public arbitrageBot;
    IQuoteManager public quoteManager;
    IPathValidator public pathValidator;
    IPathFinder public pathFinder;
    IFlashLoanManager public flashLoanManager;

    // Registry contracts
    PriceFeedRegistry public priceFeedRegistry;
    DEXRegistry public dexRegistry;

    // Component factories
    RegistryFactoryImpl public registryFactory;
    CoreComponentsFactoryImpl public coreFactory;
    ExecutionComponentsFactoryImpl public executionFactory;

    // Events
    event FactoriesDeployed(
        address registryFactory,
        address coreFactory,
        address executionFactory
    );

    event ComponentsDeployed(
        address arbitrageBot,
        address quoteManager,
        address pathValidator,
        address pathFinder,
        address flashLoanManager
    );

    // Errors
    error DeploymentFailed();
    error InvalidAddress();

    constructor() {
        // Deploy factories
        registryFactory = new RegistryFactoryImpl();
        coreFactory = new CoreComponentsFactoryImpl();
        executionFactory = new ExecutionComponentsFactoryImpl();

        // Transfer ownership
        registryFactory.transferOwnership(owner());
        coreFactory.transferOwnership(owner());
        executionFactory.transferOwnership(owner());

        emit FactoriesDeployed(
            address(registryFactory),
            address(coreFactory),
            address(executionFactory)
        );
    }

    // @CRITICAL: Deploy all components
    function deployComponents(
        address _aaveAddressProvider,
        uint256 _defaultMinProfitBasisPoints,
        uint256 _defaultMaxTradeSize,
        uint256 _emergencyWithdrawalDelay
    ) external onlyOwner {
        // Deploy registries
        (address priceFeed, address dex) = registryFactory.deployRegistries();
        priceFeedRegistry = PriceFeedRegistry(priceFeed);
        dexRegistry = DEXRegistry(dex);

        // Deploy core components
        (
            address quoteManagerAddr,
            address pathValidatorAddr,
            address pathFinderAddr
        ) = coreFactory.deployCoreComponents(dex);

        quoteManager = IQuoteManager(quoteManagerAddr);
        pathValidator = IPathValidator(pathValidatorAddr);
        pathFinder = IPathFinder(pathFinderAddr);

        // Deploy execution components
        (
            address arbitrageBotAddr,
            address flashLoanManagerAddr
        ) = executionFactory.deployExecutionComponents(
            priceFeed,
            dex,
            _aaveAddressProvider,
            _defaultMinProfitBasisPoints,
            _defaultMaxTradeSize,
            _emergencyWithdrawalDelay
        );

        arbitrageBot = IMultiPathArbitrage(arbitrageBotAddr);
        flashLoanManager = IFlashLoanManager(flashLoanManagerAddr);

        emit ComponentsDeployed(
            arbitrageBotAddr,
            quoteManagerAddr,
            pathValidatorAddr,
            pathFinderAddr,
            flashLoanManagerAddr
        );
    }

    // @CRITICAL: Update component addresses if needed
    function updateComponent(
        string memory component,
        address newAddress
    ) external onlyOwner {
        if (newAddress == address(0)) revert InvalidAddress();

        bytes32 componentHash = keccak256(abi.encodePacked(component));

        if (componentHash == keccak256("arbitrageBot")) {
            arbitrageBot = IMultiPathArbitrage(newAddress);
        } else if (componentHash == keccak256("quoteManager")) {
            quoteManager = IQuoteManager(newAddress);
        } else if (componentHash == keccak256("pathValidator")) {
            pathValidator = IPathValidator(newAddress);
        } else if (componentHash == keccak256("pathFinder")) {
            pathFinder = IPathFinder(newAddress);
        } else if (componentHash == keccak256("flashLoanManager")) {
            flashLoanManager = IFlashLoanManager(newAddress);
        } else if (componentHash == keccak256("priceFeedRegistry")) {
            priceFeedRegistry = PriceFeedRegistry(newAddress);
        } else if (componentHash == keccak256("dexRegistry")) {
            dexRegistry = DEXRegistry(newAddress);
        } else {
            revert("Invalid component name");
        }
    }

    // Get all component addresses
    function getComponents() external view returns (
        address[] memory addresses,
        string[] memory names
    ) {
        addresses = new address[](7);
        names = new string[](7);

        addresses[0] = address(arbitrageBot);
        addresses[1] = address(quoteManager);
        addresses[2] = address(pathValidator);
        addresses[3] = address(pathFinder);
        addresses[4] = address(flashLoanManager);
        addresses[5] = address(priceFeedRegistry);
        addresses[6] = address(dexRegistry);

        names[0] = "arbitrageBot";
        names[1] = "quoteManager";
        names[2] = "pathValidator";
        names[3] = "pathFinder";
        names[4] = "flashLoanManager";
        names[5] = "priceFeedRegistry";
        names[6] = "dexRegistry";
    }
}
