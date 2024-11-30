"""
Check Bitcoin address balance using public blockchain APIs
"""
import requests
from typing import Dict, Any, Optional, TypedDict, Union, cast
from decimal import Decimal
from dotenv import load_dotenv
import os

from configs.logging_config import get_logger

logger = get_logger(__name__)

class BTCBalance(TypedDict):
    """Type definition for Bitcoin balance information."""
    balance: Decimal
    received: Decimal
    spent: Decimal
    tx_count: int

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

def get_balance_blockstream(address: str) -> Optional[BTCBalance]:
    """
    Get Bitcoin balance using Blockstream API.
    
    Args:
        address: Bitcoin address to check
        
    Returns:
        Balance information if successful, None if failed
    """
    try:
        # Get address info
        response = requests.get(f'https://blockstream.info/api/address/{address}')
        response.raise_for_status()
        data = response.json()
        
        # Get transaction history
        tx_response = requests.get(f'https://blockstream.info/api/address/{address}/txs')
        tx_response.raise_for_status()
        
        return BTCBalance(
            balance=Decimal(str(data.get('chain_stats', {}).get('funded_txo_sum', 0) - 
                               data.get('chain_stats', {}).get('spent_txo_sum', 0))) / Decimal('100000000'),
            received=Decimal(str(data.get('chain_stats', {}).get('funded_txo_sum', 0))) / Decimal('100000000'),
            spent=Decimal(str(data.get('chain_stats', {}).get('spent_txo_sum', 0))) / Decimal('100000000'),
            tx_count=data.get('chain_stats', {}).get('tx_count', 0)
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error checking Blockstream: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error checking Blockstream: {str(e)}")
        return None

def get_balance_blockchain_info(address: str) -> Optional[BTCBalance]:
    """
    Get Bitcoin balance using Blockchain.info API.
    
    Args:
        address: Bitcoin address to check
        
    Returns:
        Balance information if successful, None if failed
    """
    try:
        response = requests.get(f'https://blockchain.info/rawaddr/{address}')
        response.raise_for_status()
        data = response.json()
        
        return BTCBalance(
            balance=Decimal(str(data.get('final_balance', 0))) / Decimal('100000000'),
            received=Decimal(str(data.get('total_received', 0))) / Decimal('100000000'),
            spent=Decimal(str(data.get('total_sent', 0))) / Decimal('100000000'),
            tx_count=data.get('n_tx', 0)
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error checking Blockchain.info: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error checking Blockchain.info: {str(e)}")
        return None

def check_balance(address: str) -> Optional[BTCBalance]:
    """
    Check Bitcoin balance using multiple APIs for redundancy.
    
    Args:
        address: Bitcoin address to check
        
    Returns:
        Balance information if successful, None if all APIs fail
    """
    # Try Blockstream first
    balance = get_balance_blockstream(address)
    if balance:
        logger.info("Successfully retrieved balance from Blockstream")
        return balance
        
    # Fallback to Blockchain.info
    logger.info("Falling back to Blockchain.info...")
    balance = get_balance_blockchain_info(address)
    if balance:
        logger.info("Successfully retrieved balance from Blockchain.info")
        return balance
        
    logger.error("Failed to retrieve balance from all APIs")
    return None

def format_balance(balance: BTCBalance) -> None:
    """
    Log formatted balance information.
    
    Args:
        balance: Balance information to format and log
    """
    logger.info("\nBitcoin Address Balance:")
    logger.info(f"Current Balance: {balance['balance']:.8f} BTC")
    logger.info(f"Total Received: {balance['received']:.8f} BTC")
    logger.info(f"Total Spent: {balance['spent']:.8f} BTC")
    logger.info(f"Transaction Count: {balance['tx_count']}")

def main() -> None:
    """Main function to check Bitcoin address balance."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Bitcoin address from environment or use default
        address = os.getenv('BTC_ADDRESS', '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa')  # Satoshi's address as default
        logger.info(f"Checking balance for address: {address}")
        
        # Get and display balance
        balance = check_balance(address)
        if balance:
            format_balance(balance)
        
    except ValueError as e:
        logger.error(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
