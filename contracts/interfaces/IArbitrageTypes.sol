// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// @CONTEXT: Common types used across arbitrage interfaces
// @CRITICAL: Shared type definitions to avoid duplication

interface IArbitrageTypes {
    // Common path and step definitions
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
        address[] tokens;  // Combined from IPathFinder
        address[] dexes;  // Combined from IPathFinder
    }

    // Quote-related types
    struct DEXQuote {
        address dex;
        uint256 output;
        uint256 gasEstimate;
        bool isV3;
        address targetToken;
        uint256 priceImpact;
        uint256 liquidity;
    }

    // Validation types
    struct PathValidation {
        bool isValid;
        uint256[] expectedOutputs;
        uint256[] minOutputs;
        uint256 totalGas;
        uint256 minProfit;
        uint256 maxProfit;
    }

    // Flash loan types
    struct FlashLoanParams {
        address[] tokens;
        address[] dexes;
        uint256 amount;
        uint256 minProfit;
    }
}
