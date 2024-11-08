// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IPriceFeed.sol";

// @CONTEXT: Registry for managing Chainlink price feed connections
// @CRITICAL: Central source of price data for arbitrage calculations
contract PriceFeedRegistry is Ownable {
    // Mapping from token pair hash to price feed address
    mapping(bytes32 => address) public priceFeeds;

    // Mapping to track stale price thresholds (in seconds)
    mapping(address => uint256) public stalePriceThresholds;

    // Default stale price threshold (1 hour)
    uint256 public constant DEFAULT_STALE_THRESHOLD = 1 hours;

    // Events
    event PriceFeedRegistered(address baseToken, address quoteToken, address feed);
    event PriceFeedRemoved(address baseToken, address quoteToken);
    event StalePriceThresholdUpdated(address feed, uint256 threshold);

    // Errors
    error InvalidPriceFeed();
    error StalePrice(uint256 lastUpdate, uint256 threshold);
    error PriceFeedNotFound();
    error InvalidThreshold();

    // @CRITICAL: Register a new price feed for a token pair
    function registerPriceFeed(
        address baseToken,
        address quoteToken,
        address feed,
        uint256 stalePriceThreshold
    ) external onlyOwner {
        if (feed == address(0)) revert InvalidPriceFeed();
        if (stalePriceThreshold == 0) revert InvalidThreshold();

        bytes32 pairHash = _getPairHash(baseToken, quoteToken);
        priceFeeds[pairHash] = feed;
        stalePriceThresholds[feed] = stalePriceThreshold;

        emit PriceFeedRegistered(baseToken, quoteToken, feed);
        emit StalePriceThresholdUpdated(feed, stalePriceThreshold);
    }

    // Remove a price feed
    function removePriceFeed(
        address baseToken,
        address quoteToken
    ) external onlyOwner {
        bytes32 pairHash = _getPairHash(baseToken, quoteToken);
        delete priceFeeds[pairHash];
        emit PriceFeedRemoved(baseToken, quoteToken);
    }

    // @CRITICAL: Get the latest price with safety checks
    function getPrice(
        address baseToken,
        address quoteToken
    ) external view returns (uint256 price, uint8 decimals) {
        bytes32 pairHash = _getPairHash(baseToken, quoteToken);
        address feed = priceFeeds[pairHash];
        if (feed == address(0)) revert PriceFeedNotFound();

        IPriceFeed priceFeed = IPriceFeed(feed);
        (
            ,
            int256 answer,
            ,
            uint256 updatedAt,

        ) = priceFeed.latestRoundData();

        // Check for stale price
        uint256 threshold = stalePriceThresholds[feed];
        if (block.timestamp - updatedAt > threshold) {
            revert StalePrice(updatedAt, threshold);
        }

        if (answer <= 0) revert InvalidPriceFeed();

        return (uint256(answer), priceFeed.decimals());
    }

    // Update stale price threshold for a feed
    function updateStalePriceThreshold(
        address feed,
        uint256 threshold
    ) external onlyOwner {
        if (threshold == 0) revert InvalidThreshold();
        stalePriceThresholds[feed] = threshold;
        emit StalePriceThresholdUpdated(feed, threshold);
    }

    // Internal function to generate pair hash
    function _getPairHash(
        address baseToken,
        address quoteToken
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(baseToken, quoteToken));
    }

    // View function to check if price feed exists
    function hasPriceFeed(
        address baseToken,
        address quoteToken
    ) external view returns (bool) {
        bytes32 pairHash = _getPairHash(baseToken, quoteToken);
        return priceFeeds[pairHash] != address(0);
    }

    // Get price feed address for a pair
    function getPriceFeed(
        address baseToken,
        address quoteToken
    ) external view returns (address) {
        bytes32 pairHash = _getPairHash(baseToken, quoteToken);
        return priceFeeds[pairHash];
    }
}
