// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title CrossChainBridge
 * @notice Bridge contract for handling cross-chain atomic swaps
 * @dev Implements message verification and relaying between chains
 */
contract CrossChainBridge is Ownable, ReentrancyGuard, Pausable {
    // Chain configuration
    struct ChainConfig {
        bool enabled;
        uint256 requiredConfirmations;
        uint256 gasLimit;
        address swapContract;
    }

    // Message status
    enum MessageStatus { PENDING, PROCESSED, FAILED }

    // Cross-chain message
    struct CrossChainMessage {
        uint256 sourceChainId;
        uint256 destinationChainId;
        bytes32 swapId;
        address initiator;
        uint256 timestamp;
        MessageStatus status;
        bytes signature;
    }

    // State variables
    mapping(uint256 => ChainConfig) public chainConfigs;
    mapping(bytes32 => CrossChainMessage) public messages;
    mapping(address => bool) public authorizedRelayers;

    uint256 public messageNonce;
    uint256 public minConfirmationBlocks;

    // Events
    event MessageSent(bytes32 indexed messageId, uint256 indexed sourceChainId, uint256 indexed destinationChainId, bytes32 swapId);
    event MessageProcessed(bytes32 indexed messageId, MessageStatus status);
    event ChainConfigUpdated(uint256 indexed chainId, bool enabled, uint256 confirmations, uint256 gasLimit, address swapContract);
    event RelayerUpdated(address indexed relayer, bool authorized);

    // Errors
    error InvalidChainConfig();
    error InvalidRelayer();
    error InvalidMessage();
    error MessageAlreadyProcessed();
    error InsufficientConfirmations();

    // Modifiers
    modifier onlyAuthorizedRelayer() {
        if (!authorizedRelayers[msg.sender]) revert InvalidRelayer();
        _;
    }

    modifier validChain(uint256 chainId) {
        if (!chainConfigs[chainId].enabled) revert InvalidChainConfig();
        _;
    }

    constructor(uint256 _minConfirmationBlocks) {
        minConfirmationBlocks = _minConfirmationBlocks;
        authorizedRelayers[msg.sender] = true;
    }

    /**
     * @notice Configure a chain for cross-chain communication
     * @param chainId Chain ID to configure
     * @param confirmations Required confirmations for this chain
     * @param gasLimit Gas limit for transactions on this chain
     * @param swapContract Address of the swap contract on this chain
     */
    function configureChain(
        uint256 chainId,
        uint256 confirmations,
        uint256 gasLimit,
        address swapContract
    ) external onlyOwner {
        require(chainId != 0, "Invalid chain ID");
        require(swapContract != address(0), "Invalid swap contract");
        require(confirmations > 0, "Invalid confirmations");
        require(gasLimit > 0, "Invalid gas limit");

        chainConfigs[chainId] = ChainConfig({
            enabled: true,
            requiredConfirmations: confirmations,
            gasLimit: gasLimit,
            swapContract: swapContract
        });

        emit ChainConfigUpdated(chainId, true, confirmations, gasLimit, swapContract);
    }

    /**
     * @notice Update relayer authorization
     * @param relayer Address of the relayer
     * @param authorized Authorization status
     */
    function updateRelayer(address relayer, bool authorized) external onlyOwner {
        require(relayer != address(0), "Invalid relayer address");
        authorizedRelayers[relayer] = authorized;
        emit RelayerUpdated(relayer, authorized);
    }

    /**
     * @notice Send a cross-chain message
     * @param destinationChainId Target chain ID
     * @param swapId Swap ID to relay
     */
    function sendMessage(
        uint256 destinationChainId,
        bytes32 swapId
    ) external validChain(destinationChainId) nonReentrant whenNotPaused {
        bytes32 messageId = generateMessageId(block.chainid, destinationChainId, swapId, messageNonce++);

        messages[messageId] = CrossChainMessage({
            sourceChainId: block.chainid,
            destinationChainId: destinationChainId,
            swapId: swapId,
            initiator: msg.sender,
            timestamp: block.timestamp,
            status: MessageStatus.PENDING,
            signature: ""
        });

        emit MessageSent(messageId, block.chainid, destinationChainId, swapId);
    }

    /**
     * @notice Process a received cross-chain message
     * @param messageId ID of the message to process
     * @param signature Signature proving message validity
     */
    function processMessage(
        bytes32 messageId,
        bytes calldata signature
    ) external onlyAuthorizedRelayer nonReentrant whenNotPaused {
        CrossChainMessage storage message = messages[messageId];

        if (message.status != MessageStatus.PENDING) revert MessageAlreadyProcessed();
        if (block.number < message.timestamp + minConfirmationBlocks) revert InsufficientConfirmations();

        // Verify signature
        require(verifyMessageSignature(messageId, signature), "Invalid signature");

        // Update message status
        message.status = MessageStatus.PROCESSED;
        message.signature = signature;

        emit MessageProcessed(messageId, MessageStatus.PROCESSED);
    }

    /**
     * @notice Generate a unique message ID
     * @param sourceChainId Source chain ID
     * @param destinationChainId Destination chain ID
     * @param swapId Swap ID
     * @param nonce Message nonce
     */
    function generateMessageId(
        uint256 sourceChainId,
        uint256 destinationChainId,
        bytes32 swapId,
        uint256 nonce
    ) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(
            sourceChainId,
            destinationChainId,
            swapId,
            nonce
        ));
    }

    /**
     * @notice Verify a message signature
     * @param messageId Message ID
     * @param signature Signature to verify
     */
    function verifyMessageSignature(
        bytes32 messageId,
        bytes memory signature
    ) public view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(
            "\x19Ethereum Signed Message:\n32",
            messageId
        ));

        address signer = recoverSigner(messageHash, signature);
        return authorizedRelayers[signer];
    }

    /**
     * @notice Recover signer from signature
     * @param messageHash Hash of the message
     * @param signature Signature to recover from
     */
    function recoverSigner(
        bytes32 messageHash,
        bytes memory signature
    ) internal pure returns (address) {
        require(signature.length == 65, "Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }

        if (v < 27) {
            v += 27;
        }

        require(v == 27 || v == 28, "Invalid signature 'v' value");

        return ecrecover(messageHash, v, r, s);
    }

    /**
     * @notice Pause the bridge
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpause the bridge
     */
    function unpause() external onlyOwner {
        _unpause();
    }
}
