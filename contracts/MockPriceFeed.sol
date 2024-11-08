// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MockPriceFeed {
    // Price data structure
    struct PriceData {
        uint256 price;
        uint256 timestamp;
        uint8 decimals;
        bool isActive;
    }

    // State variables
    mapping(address => PriceData) public prices;
    address public owner;

    // Events
    event PriceUpdated(address indexed token, uint256 price, uint256 timestamp);
    event TokenDeactivated(address indexed token);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // Errors
    error OnlyOwner();
    error InvalidToken();
    error InvalidPrice();
    error TokenNotActive();
    error PriceNotSet();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // Admin functions
    function setPrice(
        address token,
        uint256 price,
        uint8 decimals
    ) external onlyOwner {
        if (token == address(0)) revert InvalidToken();
        if (price == 0) revert InvalidPrice();

        prices[token] = PriceData({
            price: price,
            timestamp: block.timestamp,
            decimals: decimals,
            isActive: true
        });

        emit PriceUpdated(token, price, block.timestamp);
    }

    function deactivateToken(address token) external onlyOwner {
        if (!prices[token].isActive) revert TokenNotActive();
        prices[token].isActive = false;
        emit TokenDeactivated(token);
    }

    // View functions
    function getLatestPrice(
        address token
    ) external view returns (uint256 price, uint256 timestamp) {
        PriceData memory data = prices[token];
        if (!data.isActive) revert TokenNotActive();
        if (data.price == 0) revert PriceNotSet();

        return (data.price, data.timestamp);
    }

    function getPriceFeedInfo(
        address token
    ) external view returns (
        uint256 price,
        uint8 decimals,
        bool isActive
    ) {
        PriceData memory data = prices[token];
        return (data.price, data.decimals, data.isActive);
    }

    function isTokenActive(address token) external view returns (bool) {
        return prices[token].isActive;
    }

    // Transfer ownership
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "New owner is the zero address");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }
}
