// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// @CONTEXT: Interface for Chainlink price feeds
// @CRITICAL: Used for live price data instead of mocks
interface IPriceFeed {
    function decimals() external view returns (uint8);
    function description() external view returns (string memory);
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
}
