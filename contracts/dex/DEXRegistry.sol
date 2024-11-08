// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "../interfaces/IDEXRegistry.sol";

contract DEXRegistry is IDEXRegistry {
    // DEX info mapping
    mapping(address => DEXInfo) public override dexes;

    // Gas overhead per DEX
    mapping(address => uint256) public override gasOverhead;

    // Active DEX list
    address[] public override activeDEXList;

    // Supported token pairs per DEX
    mapping(address => mapping(address => mapping(address => bool))) private supportedPairs;

    // Owner
    address public owner;

    // Events
    event DEXRegistered(address indexed dex, string protocol, uint256 maxSlippage);
    event DEXDeactivated(address indexed dex);
    event PairAdded(address indexed dex, address indexed baseToken, address indexed quoteToken);
    event PairRemoved(address indexed dex, address indexed baseToken, address indexed quoteToken);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // Errors
    error OnlyOwner();
    error DEXNotRegistered();
    error DEXAlreadyRegistered();
    error PairNotSupported();
    error InvalidParameters();
    error InvalidOwner();

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // @CRITICAL: Transfer ownership
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert InvalidOwner();
        address oldOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }

    // @CRITICAL: Register a new DEX
    function registerDEX(
        address dex,
        string memory protocol,
        uint256 maxSlippage,
        uint256 overhead
    ) external onlyOwner {
        if (dexes[dex].router != address(0)) revert DEXAlreadyRegistered();
        if (maxSlippage == 0) revert InvalidParameters();

        dexes[dex] = DEXInfo({
            router: dex,
            protocol: protocol,
            maxSlippage: maxSlippage,
            isActive: true
        });

        gasOverhead[dex] = overhead;
        activeDEXList.push(dex);

        emit DEXRegistered(dex, protocol, maxSlippage);
    }

    // @CRITICAL: Deactivate a DEX
    function deactivateDEX(address dex) external onlyOwner {
        if (dexes[dex].router == address(0)) revert DEXNotRegistered();

        dexes[dex].isActive = false;

        // Remove from active list
        for (uint256 i = 0; i < activeDEXList.length; i++) {
            if (activeDEXList[i] == dex) {
                activeDEXList[i] = activeDEXList[activeDEXList.length - 1];
                activeDEXList.pop();
                break;
            }
        }

        emit DEXDeactivated(dex);
    }

    // @CRITICAL: Add supported token pair
    function addSupportedPair(
        address dex,
        address baseToken,
        address quoteToken
    ) external onlyOwner {
        if (dexes[dex].router == address(0)) revert DEXNotRegistered();

        supportedPairs[dex][baseToken][quoteToken] = true;
        supportedPairs[dex][quoteToken][baseToken] = true;

        emit PairAdded(dex, baseToken, quoteToken);
    }

    // @CRITICAL: Remove supported token pair
    function removeSupportedPair(
        address dex,
        address baseToken,
        address quoteToken
    ) external onlyOwner {
        if (dexes[dex].router == address(0)) revert DEXNotRegistered();

        supportedPairs[dex][baseToken][quoteToken] = false;
        supportedPairs[dex][quoteToken][baseToken] = false;

        emit PairRemoved(dex, baseToken, quoteToken);
    }

    // @CRITICAL: Check if pair is supported
    function isPairSupported(
        address dex,
        address baseToken,
        address quoteToken
    ) external view override returns (bool) {
        return supportedPairs[dex][baseToken][quoteToken] ||
               supportedPairs[dex][quoteToken][baseToken];
    }

    // @CRITICAL: Validate trade
    function validateTrade(
        address dex,
        address baseToken,
        address quoteToken
    ) external view override {
        if (!dexes[dex].isActive) revert DEXNotRegistered();
        if (!supportedPairs[dex][baseToken][quoteToken] &&
            !supportedPairs[dex][quoteToken][baseToken]) {
            revert PairNotSupported();
        }
    }

    // @CRITICAL: Get active DEXes
    function getActiveDEXes() external view override returns (address[] memory) {
        return activeDEXList;
    }

    // @CRITICAL: Get DEX info
    function getDEXInfo(address dex) external view override returns (
        string memory protocol,
        uint256 maxSlippage,
        bool isActive,
        uint256 overhead
    ) {
        DEXInfo memory info = dexes[dex];
        return (
            info.protocol,
            info.maxSlippage,
            info.isActive,
            gasOverhead[dex]
        );
    }
}
