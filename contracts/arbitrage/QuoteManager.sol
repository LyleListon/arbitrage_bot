// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "../interfaces/IERC20.sol";
import "../interfaces/IQuoteManager.sol";
import "../interfaces/IUniswapV3Router.sol";
import "../interfaces/IUniswapV3Factory.sol";
import "../interfaces/IUniswapV3Pool.sol";
import "../interfaces/IDEXRegistry.sol";
import "../interfaces/IUniswapV3QuoterV2.sol";

contract QuoteManager is IQuoteManager {
    // Constants
    uint256 private constant BASIS_POINTS = 10000;
    uint256 private constant MIN_LIQUIDITY_USD = 10000; // $10k minimum liquidity
    uint256 private constant MAX_PRICE_IMPACT = 100; // 1% max price impact

    // Fee tiers
    uint24[] private FEE_TIERS = [500, 3000, 10000]; // 0.05%, 0.3%, 1%

    // Registry contract
    IDEXRegistry public dexRegistry;

    // Liquidity thresholds per token
    mapping(address => uint256) public liquidityThresholds;

    // Owner
    address public owner;

    // Events
    event QuoteGenerated(
        address dex,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        uint256 priceImpact,
        uint256 liquidity
    );

    event LiquidityThresholdUpdated(
        address token,
        uint256 threshold
    );

    // Errors
    error InsufficientLiquidity();
    error ExcessivePriceImpact();
    error UnsupportedDEX();
    error NoValidPool();
    error OnlyOwner();
    error PoolError();
    error InvalidPool();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor(address _dexRegistry) {
        dexRegistry = IDEXRegistry(_dexRegistry);
        owner = msg.sender;
    }

    // @CRITICAL: Get quotes from multiple DEXes
    function getQuotes(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external override returns (DEXQuote[] memory) {
        // Get active DEXes
        address[] memory dexes = dexRegistry.getActiveDEXes();
        DEXQuote[] memory quotes = new DEXQuote[](dexes.length * FEE_TIERS.length);
        uint256 validQuotes = 0;

        for (uint256 i = 0; i < dexes.length; i++) {
            address dex = dexes[i];

            // Skip if pair not supported
            if (!dexRegistry.isPairSupported(dex, tokenIn, tokenOut)) {
                continue;
            }

            // Skip if gas cost too high
            uint256 gasEstimate = dexRegistry.gasOverhead(dex);
            if (gasEstimate * maxGasPrice > amountIn / 100) {
                continue;
            }

            // Try each fee tier
            for (uint256 j = 0; j < FEE_TIERS.length; j++) {
                try this.getDEXQuote(dex, tokenIn, tokenOut, amountIn) returns (DEXQuote memory quote) {
                    quotes[validQuotes++] = quote;

                    emit QuoteGenerated(
                        dex,
                        tokenIn,
                        tokenOut,
                        amountIn,
                        quote.output,
                        quote.priceImpact,
                        quote.liquidity
                    );
                } catch {
                    continue;
                }
            }
        }

        // Resize array to actual quote count
        assembly {
            mstore(quotes, validQuotes)
        }

        return quotes;
    }

    // @CRITICAL: Get quote from specific DEX with liquidity analysis
    function getDEXQuote(
        address dex,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) external override returns (DEXQuote memory) {
        // Validate DEX
        if (!dexRegistry.isPairSupported(dex, tokenIn, tokenOut)) {
            revert UnsupportedDEX();
        }

        uint256 bestOutput = 0;
        uint256 bestGasEstimate = 0;
        uint256 bestLiquidity = 0;
        uint24 bestFeeTier = 0;

        // Try each fee tier
        for (uint256 i = 0; i < FEE_TIERS.length; i++) {
            uint24 feeTier = FEE_TIERS[i];
            address pool;
            try IUniswapV3Factory(dex).getPool(tokenIn, tokenOut, feeTier) returns (address _pool) {
                pool = _pool;
                if (pool == address(0)) continue;
            } catch {
                continue;
            }

            // Get pool liquidity
            uint128 liquidity;
            try IUniswapV3Pool(pool).liquidity() returns (uint128 _liquidity) {
                liquidity = _liquidity;
            } catch {
                continue;
            }

            // Check liquidity
            uint256 liquidityThreshold = liquidityThresholds[tokenIn];
            if (liquidityThreshold == 0) {
                liquidityThreshold = MIN_LIQUIDITY_USD;
            }

            if (uint256(liquidity) < liquidityThreshold) continue;

            // Get quote from QuoterV2 - Updated Sepolia address
            address quoterV2 = 0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6;
            try IUniswapV3QuoterV2(quoterV2).quoteExactInputSingle(
                tokenIn,
                tokenOut,
                feeTier,
                amountIn,
                0
            ) returns (
                uint256 amountOut,
                uint160,
                uint32,
                uint256 gasEstimate
            ) {
                if (amountOut > bestOutput) {
                    bestOutput = amountOut;
                    bestGasEstimate = gasEstimate;
                    bestLiquidity = uint256(liquidity);
                    bestFeeTier = feeTier;
                }
            } catch {
                continue;
            }
        }

        if (bestOutput == 0) revert NoValidPool();

        return DEXQuote({
            dex: dex,
            output: bestOutput,
            gasEstimate: bestGasEstimate + dexRegistry.gasOverhead(dex),
            isV3: true,
            targetToken: tokenOut,
            priceImpact: 0, // QuoterV2 handles slippage internally
            liquidity: bestLiquidity
        });
    }

    // @CRITICAL: Update liquidity threshold for token
    function setLiquidityThreshold(
        address token,
        uint256 threshold
    ) external onlyOwner {
        liquidityThresholds[token] = threshold;
        emit LiquidityThresholdUpdated(token, threshold);
    }

    // @CRITICAL: Batch update liquidity thresholds
    function batchSetLiquidityThresholds(
        address[] calldata tokens,
        uint256[] calldata thresholds
    ) external onlyOwner {
        require(tokens.length == thresholds.length, "Length mismatch");

        for (uint256 i = 0; i < tokens.length; i++) {
            liquidityThresholds[tokens[i]] = thresholds[i];
            emit LiquidityThresholdUpdated(tokens[i], thresholds[i]);
        }
    }
}
