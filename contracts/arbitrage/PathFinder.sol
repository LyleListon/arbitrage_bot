// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "../interfaces/IArbitrageComponents.sol";
import "../interfaces/IArbitrageTypes.sol";

// @CRITICAL: Advanced path finding with optimization
contract PathFinder is IPathFinder {
    // Constants
    uint256 private constant BASIS_POINTS = 10000;
    uint256 private constant MAX_PATHS = 5;
    uint256 private constant MIN_PROFIT_THRESHOLD = 50; // 0.5%
    uint256 private constant MAX_SEARCH_DEPTH = 3;

    // Contracts
    IPathValidator public pathValidator;
    IQuoteManager public quoteManager;

    // Search parameters
    uint256 public maxGasPerPath;
    uint256 public minLiquidityRequired;
    uint256 public maxPriceImpact;

    // Owner address
    address public owner;

    // Events
    event PathFound(
        address[] tokens,
        address[] dexes,
        uint256 expectedProfit,
        uint256 gasEstimate
    );

    event SearchParamsUpdated(
        uint256 maxGas,
        uint256 minLiquidity,
        uint256 maxImpact
    );

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // Errors
    error NoPathFound();
    error InvalidParams();
    error ExcessiveGas();
    error OnlyOwner();

    // Path tracking
    struct PathNode {
        address token;
        uint256 amount;
        uint256 gasUsed;
        address[] previousTokens;
        address[] previousDexes;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor(
        address _pathValidator,
        address _quoteManager
    ) {
        pathValidator = IPathValidator(_pathValidator);
        quoteManager = IQuoteManager(_quoteManager);

        maxGasPerPath = 500000;
        minLiquidityRequired = 10000e18; // 10k tokens
        maxPriceImpact = 100; // 1%

        owner = msg.sender;
    }

    // @CRITICAL: Find best arbitrage path
    function findBestPath(
        address startToken,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external override returns (IArbitrageTypes.ArbitragePath memory) {
        if (startToken == address(0) || amountIn == 0) revert InvalidParams();

        // Initialize search
        PathNode[] memory queue = new PathNode[](100);
        uint256 queueStart = 0;
        uint256 queueEnd = 0;

        // Add start node
        queue[queueEnd++] = PathNode({
            token: startToken,
            amount: amountIn,
            gasUsed: 0,
            previousTokens: new address[](0),
            previousDexes: new address[](0)
        });

        IArbitrageTypes.ArbitragePath memory bestPath;
        uint256 bestProfit = 0;

        // Process queue
        while (queueStart < queueEnd && queueStart < 100) {
            PathNode memory current = queue[queueStart++];

            // Skip if too deep
            if (current.previousTokens.length >= MAX_SEARCH_DEPTH) continue;

            // Get quotes for all possible next steps
            IArbitrageTypes.DEXQuote[] memory quotes = quoteManager.getQuotes(
                current.token,
                address(0), // Get all possible tokens
                current.amount,
                maxGasPrice
            );

            // Process each quote
            for (uint256 i = 0; i < quotes.length; i++) {
                IArbitrageTypes.DEXQuote memory quote = quotes[i];

                // Skip if gas limit exceeded
                if (current.gasUsed + quote.gasEstimate > maxGasPerPath) continue;

                // Skip if liquidity too low
                if (quote.liquidity < minLiquidityRequired) continue;

                // Skip if price impact too high
                if (quote.priceImpact > maxPriceImpact) continue;

                // Check if we can close the loop
                if (quote.targetToken == startToken) {
                    // Validate complete path
                    address[] memory pathTokens = _buildTokenPath(current, startToken);
                    address[] memory pathDexes = _buildDexPath(current, quote.dex);

                    IArbitrageTypes.PathValidation memory validation = pathValidator.validatePath(
                        pathTokens,
                        pathDexes,
                        amountIn,
                        maxGasPrice
                    );

                    if (validation.isValid && validation.maxProfit > bestProfit) {
                        bestProfit = validation.maxProfit;
                        bestPath = IArbitrageTypes.ArbitragePath({
                            steps: new IArbitrageTypes.PathStep[](0), // This needs to be properly populated
                            totalGasEstimate: validation.totalGas,
                            expectedProfit: validation.maxProfit,
                            useFlashLoan: quote.output > amountIn * 2,
                            tokens: pathTokens,
                            dexes: pathDexes
                        });

                        emit PathFound(
                            pathTokens,
                            pathDexes,
                            validation.maxProfit,
                            validation.totalGas
                        );
                    }
                    continue;
                }

                // Add to queue if not visited
                if (!_isTokenVisited(current, quote.targetToken)) {
                    queue[queueEnd++] = PathNode({
                        token: quote.targetToken,
                        amount: quote.output,
                        gasUsed: current.gasUsed + quote.gasEstimate,
                        previousTokens: _appendToken(current.previousTokens, current.token),
                        previousDexes: _appendDex(current.previousDexes, quote.dex)
                    });
                }
            }
        }

        if (bestProfit == 0) revert NoPathFound();
        return bestPath;
    }

    // @CRITICAL: Find paths with specific tokens
    function findPathsWithTokens(
        address startToken,
        address[] calldata targetTokens,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external override returns (IArbitrageTypes.ArbitragePath[] memory) {
        if (targetTokens.length == 0) revert InvalidParams();

        IArbitrageTypes.ArbitragePath[] memory paths = new IArbitrageTypes.ArbitragePath[](targetTokens.length);
        uint256 validPaths = 0;

        for (uint256 i = 0; i < targetTokens.length; i++) {
            // Find best path through this token
            try this.findBestPath(startToken, amountIn, maxGasPrice) returns (IArbitrageTypes.ArbitragePath memory path) {
                paths[validPaths++] = path;
            } catch {
                continue;
            }
        }

        // Resize array to actual path count
        assembly {
            mstore(paths, validPaths)
        }

        return paths;
    }

    // Helper functions
    function _isTokenVisited(
        PathNode memory node,
        address token
    ) private pure returns (bool) {
        if (node.token == token) return true;
        for (uint256 i = 0; i < node.previousTokens.length; i++) {
            if (node.previousTokens[i] == token) return true;
        }
        return false;
    }

    function _appendToken(
        address[] memory tokens,
        address token
    ) private pure returns (address[] memory) {
        address[] memory newTokens = new address[](tokens.length + 1);
        for (uint256 i = 0; i < tokens.length; i++) {
            newTokens[i] = tokens[i];
        }
        newTokens[tokens.length] = token;
        return newTokens;
    }

    function _appendDex(
        address[] memory dexes,
        address dex
    ) private pure returns (address[] memory) {
        address[] memory newDexes = new address[](dexes.length + 1);
        for (uint256 i = 0; i < dexes.length; i++) {
            newDexes[i] = dexes[i];
        }
        newDexes[dexes.length] = dex;
        return newDexes;
    }

    function _buildTokenPath(
        PathNode memory node,
        address endToken
    ) private pure returns (address[] memory) {
        address[] memory path = new address[](node.previousTokens.length + 2);
        for (uint256 i = 0; i < node.previousTokens.length; i++) {
            path[i] = node.previousTokens[i];
        }
        path[node.previousTokens.length] = node.token;
        path[node.previousTokens.length + 1] = endToken;
        return path;
    }

    function _buildDexPath(
        PathNode memory node,
        address lastDex
    ) private pure returns (address[] memory) {
        address[] memory path = new address[](node.previousDexes.length + 1);
        for (uint256 i = 0; i < node.previousDexes.length; i++) {
            path[i] = node.previousDexes[i];
        }
        path[node.previousDexes.length] = lastDex;
        return path;
    }

    // Update search parameters
    function updateSearchParams(
        uint256 _maxGasPerPath,
        uint256 _minLiquidityRequired,
        uint256 _maxPriceImpact
    ) external onlyOwner {
        maxGasPerPath = _maxGasPerPath;
        minLiquidityRequired = _minLiquidityRequired;
        maxPriceImpact = _maxPriceImpact;

        emit SearchParamsUpdated(
            _maxGasPerPath,
            _minLiquidityRequired,
            _maxPriceImpact
        );
    }

    // Transfer ownership
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "New owner is the zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
