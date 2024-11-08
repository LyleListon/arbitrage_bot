// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IMultiPathArbitrage {
    struct PathStep {
        address dex;
        address[] path;
        uint256 expectedOutput;
        uint256 minOutput;
        uint256 gasEstimate;
    }

    struct ArbitragePath {
        PathStep[] steps;
        uint256 totalGasEstimate;
        uint256 expectedProfit;
        bool useFlashLoan;
    }

    function executeMultiPathArbitrage(ArbitragePath calldata path, uint256 amount) external returns (bool);
}
