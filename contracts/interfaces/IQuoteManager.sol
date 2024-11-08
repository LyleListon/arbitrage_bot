// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IQuoteManager {
    struct DEXQuote {
        address dex;
        uint256 output;
        uint256 gasEstimate;
        bool isV3;
        address targetToken;
        uint256 priceImpact;
        uint256 liquidity;
    }

    function getQuotes(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 maxGasPrice
    ) external returns (DEXQuote[] memory);

    function getDEXQuote(
        address dex,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) external returns (DEXQuote memory);
}
