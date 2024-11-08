// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./IArbitrageTypes.sol";

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
