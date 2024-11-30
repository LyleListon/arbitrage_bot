from web3 import Web3
from web3.exceptions import Web3Exception
from web3.types import Wei, ChecksumAddress
from typing import List, Optional, Dict, Any, TypedDict, cast, Union
from eth_typing import HexStr
from datetime import datetime
import time
from dotenv import load_dotenv
import os

from configs.logging_config import get_logger

logger = get_logger(__name__)

class PendingTransactionInfo(TypedDict):
    """Type definition for pending transaction information."""
    from_addr: str
    value: Wei
    hash: HexStr

class TransactionInfo(TypedDict):
    """Type definition for transaction information."""
    from_addr: str
    to_addr: Optional[str]
    value: Wei
    hash: HexStr
    gas_price: Wei
    timestamp: int
    type: str  # 'incoming' or 'outgoing'

class BlockInfo(TypedDict):
    """Type definition for block information."""
    transactions: List[Dict[str, Any]]
    timestamp: int
    number: int

def get_pending_transactions(w3: Web3, address: ChecksumAddress) -> List[PendingTransactionInfo]:
    """
    Get pending transactions for the specified address.
    
    Args:
        w3: Web3 instance to use
        address: Address to check transactions for
        
    Returns:
        List of pending transactions
    """
    try:
        pending_txs: List[PendingTransactionInfo] = []
        # Cast block to our custom type that matches the actual structure
        pending_block = cast(Dict[str, List[Dict[str, Any]]], w3.eth.get_block('pending', True))
        for tx in pending_block.get('transactions', []):
            if tx.get('to') and tx['to'].lower() == address.lower():
                tx_hash = tx['hash'].hex() if isinstance(tx['hash'], bytes) else tx['hash']
                pending_txs.append({
                    'from_addr': tx['from'],
                    'value': Wei(tx['value']),
                    'hash': HexStr(tx_hash)
                })
        return pending_txs
    except Web3Exception as e:
        logger.error(f"Web3 error getting pending transactions: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting pending transactions: {str(e)}")
        return []

def create_transaction_info(tx: Dict[str, Any], block_timestamp: int) -> TransactionInfo:
    """
    Create a TransactionInfo object from raw transaction data.
    
    Args:
        tx: Transaction data
        block_timestamp: Block timestamp
        
    Returns:
        Formatted transaction data
    """
    tx_hash = tx['hash'].hex() if isinstance(tx['hash'], bytes) else tx['hash']
    return {
        'from_addr': tx['from'],
        'to_addr': tx.get('to'),
        'value': Wei(tx['value']),
        'hash': HexStr(tx_hash),
        'gas_price': Wei(tx['gasPrice']),
        'timestamp': block_timestamp,
        'type': 'unknown'  # Will be set by caller
    }

def get_historical_transactions(
    w3: Web3,
    address: ChecksumAddress,
    start_block: int,
    end_block: int
) -> List[TransactionInfo]:
    """
    Get historical transactions for the specified address within a block range.
    
    Args:
        w3: Web3 instance to use
        address: Address to check transactions for
        start_block: Starting block number
        end_block: Ending block number
        
    Returns:
        List of historical transactions
    """
    transactions: List[TransactionInfo] = []
    
    for block_num in range(start_block, end_block + 1):
        try:
            # Cast block to our custom type that matches the actual structure
            block = cast(BlockInfo, w3.eth.get_block(block_num, True))
            block_timestamp = int(block['timestamp'])
            
            for tx in block['transactions']:
                if ((tx.get('to') and tx['to'].lower() == address.lower()) or 
                    tx['from'].lower() == address.lower()):
                    tx_info = create_transaction_info(tx, block_timestamp)
                    # Set transaction type based on address comparison
                    tx_info['type'] = 'incoming' if (tx.get('to') and 
                        tx['to'].lower() == address.lower()) else 'outgoing'
                    transactions.append(tx_info)
                    
        except Web3Exception as e:
            logger.error(f"Web3 error getting block {block_num}: {str(e)}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error getting block {block_num}: {str(e)}")
            continue
            
    return transactions

def main() -> None:
    """Main function to check transactions for a specific address."""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    rpc_url = os.getenv('MAINNET_RPC_URL', 'https://eth-mainnet.g.alchemy.com/v2/kRXhWVt8YU_8LnGS20145F5uBDFbL_k0')
    raw_address = os.getenv('ETH_ADDRESS', '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801')
    address = Web3.to_checksum_address(raw_address)
    
    try:
        # Initialize web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            logger.error("Failed to connect to Ethereum network")
            return
        
        # Get current block and balance
        current_block = w3.eth.block_number
        balance = w3.eth.get_balance(address)
        logger.info(f"Current block: {current_block}")
        logger.info(f"Current balance: {w3.from_wei(balance, 'ether')} ETH")
        
        # Check pending transactions
        logger.info("\nChecking pending transactions...")
        pending_txs = get_pending_transactions(w3, address)
        for tx in pending_txs:
            logger.info("\nPending incoming transaction:")
            logger.info(f"  From: {tx['from_addr']}")
            logger.info(f"  Value: {w3.from_wei(tx['value'], 'ether')} ETH")
            logger.info(f"  Hash: {tx['hash']}")
        
        # Check historical transactions
        logger.info("\nChecking last 100 blocks for transactions...")
        start_block = max(0, current_block - 100)
        transactions = get_historical_transactions(w3, address, start_block, current_block)
        
        # Log transactions
        for tx in transactions:
            tx_time = datetime.fromtimestamp(tx['timestamp'])
            
            logger.info(f"\nTransaction at {tx_time.strftime('%Y-%m-%d %H:%M:%S')}:")
            logger.info(f"  Type: {tx['type']}")
            logger.info(f"  {'From' if tx['type'] == 'incoming' else 'To'}: "
                       f"{tx['from_addr'] if tx['type'] == 'incoming' else tx['to_addr']}")
            logger.info(f"  Value: {w3.from_wei(tx['value'], 'ether')} ETH")
            logger.info(f"  Hash: {tx['hash']}")
            logger.info(f"  Gas Price: {w3.from_wei(tx['gas_price'], 'gwei')} gwei")
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
