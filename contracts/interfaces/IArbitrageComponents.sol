// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./IArbitrageTypes.sol";

// @CRITICAL: Interfaces for arbitrage components with unified types

interface IMultiPathArbitrage {
    function executeMultiPathArbitrage(
        IArbitrageTypes.ArbitragePath calldata path,
        uint256 amount
    ) external;

    function setRegistries(address priceFeed, address dex) external;
}

interface IQuoteManager {
    function getQuotes(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external returns (IArbitrageTypes.DEXQuote[] memory);

    function getDEXQuote(
        address dex,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) external returns (IArbitrageTypes.DEXQuote memory);
}

interface IPathValidator {
    function validatePath(
        address[] calldata tokens,
        address[] calldata dexes,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external returns (IArbitrageTypes.PathValidation memory);

    function meetsMinimumProfit(
        IArbitrageTypes.PathValidation memory validation,
        uint256 minProfitBasisPoints,
        uint256 amountIn
    ) external pure returns (bool);
}

interface IPathFinder {
    function findBestPath(
        address startToken,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external returns (IArbitrageTypes.ArbitragePath memory);

    function findPathsWithTokens(
        address startToken,
        address[] calldata targetTokens,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external returns (IArbitrageTypes.ArbitragePath[] memory);
}

interface IFlashLoanManager {
    function executeWithFlashLoan(
        address token,
        uint256 amount,
        IArbitrageTypes.FlashLoanParams calldata params
    ) external;

    function calculateOptimalLoanAmount(
        address token,
        uint256 baseAmount,
        uint256 expectedProfit
    ) external pure returns (uint256);
}
