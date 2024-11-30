"""
Check pending and recent transactions for an Ethereum address
"""
from __future__ import annotations
from web3 import Web3
from web3.types import Wei, ChecksumAddress
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional, TypedDict, cast, Union
from typing import Any  # Explicitly import Any
from decimal import Decimal
from datetime import datetime

from configs.logging_config import get_logger

logger = get_logger(__name__)

class BlockInfo(TypedDict):
    """Type definition for block information."""
    timestamp: int
    transactions: List[Dict[str, Any]]
    number: int

class Transaction(TypedDict):
    """Type definition for transaction information."""
    block_number: int
    timestamp: int
    from_addr: ChecksumAddress
    to_addr: Optional[ChecksumAddress]
    value: Wei
    hash: str

def get_env_var(var_name: str) -> str:
    """
    Get environment variable with error checking.
    
    Args:
        var_name: Name of the environment variable
        
    Returns:
        Value of the environment variable
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Environment variable {var_name} not set")
    return value

def format_transaction(
    w3: Web3,
    tx: Dict[str, Any],
    block_time: int,
    block_num: int
) -> Transaction:
    """
    Format transaction data into a standard structure.
    
    Args:
        w3: Web3 instance
        tx: Raw transaction data
        block_time: Block timestamp
        block_num: Block number
        
    Returns:
        Formatted transaction data
    """
    to_addr = tx.get('to')
    return {
        'block_number': block_num,
        'timestamp': block_time,
        'from_addr': Web3.to_checksum_address(tx['from']),
        'to_addr': Web3.to_checksum_address(to_addr) if to_addr else None,
        'value': Wei(tx['value']),
        'hash': tx['hash'].hex() if isinstance(tx['hash'], bytes) else tx['hash']
    }

def get_recent_transactions(
    w3: Web3,
    address: ChecksumAddress,
    num_blocks: int = 10
) -> List[Transaction]:
    """
    Get recent transactions for an address from the last N blocks.
    
    Args:
        w3: Web3 instance
        address: Address to check
        num_blocks: Number of recent blocks to check
        
    Returns:
        List of transactions
    """
    transactions: List[Transaction] = []
    current_block = w3.eth.block_number
    
    for block_num in range(current_block - num_blocks, current_block + 1):
        try:
            block = cast(BlockInfo, w3.eth.get_block(block_num, True))
            block_time = int(block['timestamp'])
            
            for tx in block['transactions']:
                if tx.get('to') and tx['to'].lower() == address.lower():
                    tx_data = format_transaction(w3, tx, block_time, block_num)
                    transactions.append(tx_data)
                    
        except Exception as e:
            logger.error(f"Error getting block {block_num}: {str(e)}")
            continue
            
    return transactions

def format_eth_value(w3: Web3, value: Wei) -> str:
    """
    Format Wei value to ETH string with proper precision.
    
    Args:
        w3: Web3 instance
        value: Value in Wei
        
    Returns:
        Formatted string in ETH
    """
    eth_value = Decimal(str(w3.from_wei(value, 'ether')))
    return f"{eth_value:.6f} ETH"

def log_transaction(w3: Web3, tx: Transaction) -> None:
    """
    Log formatted transaction information.
    
    Args:
        w3: Web3 instance
        tx: Transaction data to log
    """
    timestamp = datetime.fromtimestamp(tx['timestamp'])
    logger.info(f"\nFound incoming transaction in block {tx['block_number']}")
    logger.info(f"Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"From: {tx['from_addr']}")
    if tx['to_addr']:
        logger.info(f"To: {tx['to_addr']}")
    logger.info(f"Value: {format_eth_value(w3, tx['value'])}")
    logger.info(f"Hash: {tx['hash']}")

def main() -> None:
    """Main function to check pending and recent transactions."""
    try:
        # Load mainnet configuration
        load_dotenv('.env.mainnet')
        
        # Get required environment variables
        try:
            rpc_url = get_env_var('MAINNET_RPC_URL')
        except ValueError as e:
            logger.error(str(e))
            return
            
        # Connect to mainnet
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            logger.error("Failed to connect to mainnet")
            return
            
        logger.info(f"Connected to mainnet: {w3.is_connected()}")
        
        # Get address from environment or use default
        raw_address = os.getenv('ETH_ADDRESS', '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801')
        address = Web3.to_checksum_address(raw_address)
        
        # Get current block
        current_block = w3.eth.block_number
        logger.info(f"\nCurrent block: {current_block}")
        
        # Check recent transactions
        logger.info("\nChecking recent blocks for incoming transactions...")
        transactions = get_recent_transactions(w3, address)
        
        if transactions:
            for tx in transactions:
                log_transaction(w3, tx)
        else:
            logger.info("No incoming transactions found in recent blocks")
        
        # Get current balance
        balance = w3.eth.get_balance(address)
        logger.info(f"\nCurrent balance: {format_eth_value(w3, balance)}")
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
