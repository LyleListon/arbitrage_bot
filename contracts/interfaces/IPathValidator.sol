// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IPathValidator {
    struct PathValidation {
        bool isValid;
        uint256[] expectedOutputs;
        uint256[] minOutputs;
        uint256 maxProfit;
        uint256 minProfit;
        uint256 totalGas;
    }

    function validatePath(
        address[] calldata tokens,
        address[] calldata dexes,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external returns (PathValidation memory validation);

    function meetsMinimumProfit(
        PathValidation memory validation,
        uint256 minProfitBasisPoints,
        uint256 amountIn
    ) external pure returns (bool);

    function estimateGasCosts(
        address[] calldata tokens,
        address[] calldata dexes
    ) external view returns (uint256);
}
