// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// @CONTEXT: Unified Uniswap interfaces
// @CRITICAL: Consistent naming and organization for DEX interfaces

interface IUniswapRouterBase {
    function factory() external pure returns (address);
    function WETH() external pure returns (address);

    // Common quote functions
    function quote(
        uint amountA,
        uint reserveA,
        uint reserveB
    ) external pure returns (uint amountB);
}

interface IUniswapV2Router is IUniswapRouterBase {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);

    function getAmountsOut(
        uint amountIn,
        address[] calldata path
    ) external view returns (uint[] memory amounts);

    function getAmountsIn(
        uint amountOut,
        address[] calldata path
    ) external view returns (uint[] memory amounts);

    // Additional V2-specific functions from original interface...
}

interface IUniswapV3Router is IUniswapRouterBase {
    struct ExactInputParams {
        bytes path;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
    }

    function exactInput(
        ExactInputParams calldata params
    ) external payable returns (uint256 amountOut);

    // Additional V3-specific functions...
}
