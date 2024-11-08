// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "../interfaces/IArbitrageComponents.sol";

// @CRITICAL: Main interface file for arbitrage components
// This file now only contains interfaces and no duplicate contract implementations

interface IArbitrageExecutor {
    function executeArbitrage(
        address[] calldata path,
        uint256 amountIn,
        uint256 minAmountOut
    ) external returns (uint256);
}

interface IArbitrageValidator {
    function validatePath(
        address[] calldata path,
        uint256 amountIn
    ) external view returns (bool);
}

interface IArbitrageQuoter {
    function getQuote(
        address[] calldata path,
        uint256 amountIn
    ) external view returns (uint256);
}
