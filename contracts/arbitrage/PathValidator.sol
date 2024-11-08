// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IArbitrageComponents.sol";
import "../interfaces/IArbitrageTypes.sol";

// @CRITICAL: Advanced path validation with safety checks
contract PathValidator is IPathValidator, Ownable {
    // Constants
    uint256 private constant BASIS_POINTS = 10000;
    uint256 private constant MAX_HOPS = 4;
    uint256 private constant MIN_LIQUIDITY_RATIO = 500; // 5% of pool liquidity
    uint256 private constant MAX_PRICE_DEVIATION = 200; // 2% from reference price
    uint256 private constant MAX_TOTAL_PRICE_IMPACT = 150; // 1.5% total impact

    // Contracts
    IQuoteManager public quoteManager;

    // Validation parameters
    uint256 public maxPriceAgeDuration;
    uint256 public minProfitThreshold;
    uint256 public maxSlippagePerHop;

    // Events
    event PathValidated(
        address[] tokens,
        address[] dexes,
        bool isValid,
        string reason
    );

    event ValidationParamsUpdated(
        uint256 maxPriceAge,
        uint256 minProfit,
        uint256 maxSlippage
    );

    // Errors
    error TooManyHops();
    error InvalidPathStructure();
    error InsufficientLiquidity();
    error ExcessivePriceDeviation();
    error ExcessivePriceImpact();
    error StalePrice();

    constructor(address _quoteManager) {
        quoteManager = IQuoteManager(_quoteManager);
        maxPriceAgeDuration = 30 minutes;
        minProfitThreshold = 50; // 0.5%
        maxSlippagePerHop = 100; // 1% per hop
    }

    // @CRITICAL: Validate complete arbitrage path
    function validatePath(
        address[] calldata tokens,
        address[] calldata dexes,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external override returns (IArbitrageTypes.PathValidation memory validation) {
        // Check path structure
        if (tokens.length != dexes.length + 1) revert InvalidPathStructure();
        if (tokens.length > MAX_HOPS + 1) revert TooManyHops();

        // Initialize validation
        validation.expectedOutputs = new uint256[](tokens.length);
        validation.minOutputs = new uint256[](dexes.length);
        validation.expectedOutputs[0] = amountIn;
        validation.isValid = true;

        // Track cumulative metrics
        uint256 totalPriceImpact;
        uint256 totalGas;

        // Validate each step
        for (uint256 i = 0; i < dexes.length; i++) {
            // Get quote for this step
            IArbitrageTypes.DEXQuote memory quote = quoteManager.getDEXQuote(
                dexes[i],
                tokens[i],
                tokens[i + 1],
                validation.expectedOutputs[i]
            );

            // Update validation metrics
            validation.expectedOutputs[i + 1] = quote.output;
            totalGas += quote.gasEstimate;
            totalPriceImpact += quote.priceImpact;

            // Check liquidity ratio
            uint256 liquidityRatio = (validation.expectedOutputs[i] * BASIS_POINTS) / quote.liquidity;
            if (liquidityRatio > MIN_LIQUIDITY_RATIO) {
                validation.isValid = false;
                emit PathValidated(tokens, dexes, false, "Insufficient liquidity");
                return validation;
            }

            // Check price impact
            if (totalPriceImpact > MAX_TOTAL_PRICE_IMPACT) {
                validation.isValid = false;
                emit PathValidated(tokens, dexes, false, "Excessive price impact");
                return validation;
            }

            // Calculate minimum output for this step
            validation.minOutputs[i] = (quote.output * (BASIS_POINTS - maxSlippagePerHop)) / BASIS_POINTS;
        }

        // Calculate expected profit
        if (tokens[0] == tokens[tokens.length - 1]) {
            uint256 expectedProfit = validation.expectedOutputs[tokens.length - 1] > amountIn ?
                validation.expectedOutputs[tokens.length - 1] - amountIn : 0;

            // Account for gas costs
            uint256 gasCost = totalGas * maxGasPrice;
            validation.maxProfit = expectedProfit > gasCost ? expectedProfit - gasCost : 0;

            // Apply safety margin for minimum profit
            validation.minProfit = (validation.maxProfit * 95) / 100; // 95% of max profit
        }

        validation.totalGas = totalGas;

        emit PathValidated(
            tokens,
            dexes,
            validation.isValid,
            validation.isValid ? "Valid path" : "Invalid path"
        );
    }

    // @CRITICAL: Check if path meets minimum profit requirements
    function meetsMinimumProfit(
        IArbitrageTypes.PathValidation memory validation,
        uint256 minProfitBasisPoints,
        uint256 amountIn
    ) external pure override returns (bool) {
        if (!validation.isValid) return false;

        uint256 minRequiredProfit = (amountIn * minProfitBasisPoints) / BASIS_POINTS;
        return validation.minProfit >= minRequiredProfit;
    }

    // @CRITICAL: Update validation parameters
    function updateValidationParams(
        uint256 _maxPriceAgeDuration,
        uint256 _minProfitThreshold,
        uint256 _maxSlippagePerHop
    ) external onlyOwner {
        maxPriceAgeDuration = _maxPriceAgeDuration;
        minProfitThreshold = _minProfitThreshold;
        maxSlippagePerHop = _maxSlippagePerHop;

        emit ValidationParamsUpdated(
            _maxPriceAgeDuration,
            _minProfitThreshold,
            _maxSlippagePerHop
        );
    }

    // @CRITICAL: Validate price freshness
    function _validatePriceFreshness(uint256 timestamp) private view returns (bool) {
        return block.timestamp - timestamp <= maxPriceAgeDuration;
    }

    // @CRITICAL: Calculate cumulative price impact
    function _calculateCumulativeImpact(
        uint256[] memory impacts
    ) private pure returns (uint256) {
        uint256 totalImpact = 0;
        for (uint256 i = 0; i < impacts.length; i++) {
            totalImpact += impacts[i];
        }
        return totalImpact;
    }

    // @CRITICAL: Estimate gas costs
    function estimateGasCosts(
        address[] calldata tokens,
        address[] calldata dexes
    ) external returns (uint256) {
        uint256 totalGas = 0;

        for (uint256 i = 0; i < dexes.length; i++) {
            IArbitrageTypes.DEXQuote memory quote = quoteManager.getDEXQuote(
                dexes[i],
                tokens[i],
                tokens[i + 1],
                1e18 // Use 1 token as baseline for gas estimate
            );
            totalGas += quote.gasEstimate;
        }

        return totalGas;
    }
}
