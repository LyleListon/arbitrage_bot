"""
Check Ethereum address transactions and balance using Etherscan API
"""
from __future__ import annotations
import requests
import os
from dotenv import load_dotenv
import time
from typing import Dict, List, Optional, TypedDict, Any, cast, Union, Mapping
from decimal import Decimal
from datetime import datetime
from requests.models import PreparedRequest

from configs.logging_config import get_logger

logger = get_logger(__name__)

class Transaction(TypedDict):
    """Type definition for transaction information."""
    timeStamp: str
    from_addr: str
    to: str
    value: str
    hash: str
    txreceipt_status: str

class EtherscanResponse(TypedDict):
    """Type definition for Etherscan API response."""
    status: str
    message: str
    result: Union[List[Dict[str, Any]], str]

def get_etherscan_api_key() -> str:
    """Get Etherscan API key from environment variables."""
    api_key = os.getenv('ETHERSCAN_API_KEY')
    if not api_key:
        raise ValueError("ETHERSCAN_API_KEY environment variable not set")
    return api_key

def create_params(base_params: Dict[str, Any], api_key: str) -> Mapping[str, str]:
    """
    Create properly typed parameters for Etherscan API request.
    
    Args:
        base_params: Base parameters for the request
        api_key: Etherscan API key
        
    Returns:
        Dictionary of parameters with proper string typing
    """
    return {
        **{k: str(v) for k, v in base_params.items()},
        'apikey': api_key
    }

def get_transactions(address: str, api_key: str) -> Optional[List[Transaction]]:
    """
    Get latest transactions for an address from Etherscan.
    
    Args:
        address: Ethereum address to check
        api_key: Etherscan API key
        
    Returns:
        List of transactions if successful, None if failed
    """
    api_url = 'https://api.etherscan.io/api'
    base_params = {
        'module': 'account',
        'action': 'txlist',
        'address': address,
        'startblock': 0,
        'endblock': 99999999,
        'page': 1,
        'offset': 10,
        'sort': 'desc'
    }
    
    try:
        params = create_params(base_params, api_key)
        response = requests.get(api_url, params=cast(Dict[str, str], params))
        response.raise_for_status()
        
        data = cast(EtherscanResponse, response.json())
        if data['status'] == '1':
            return cast(List[Transaction], data['result'])
        else:
            logger.error(f"Etherscan API error: {data['message']}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error checking transactions: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error checking transactions: {str(e)}")
        return None

def get_balance(address: str, api_key: str) -> Optional[Decimal]:
    """
    Get current balance for an address from Etherscan.
    
    Args:
        address: Ethereum address to check
        api_key: Etherscan API key
        
    Returns:
        Balance in ETH if successful, None if failed
    """
    api_url = 'https://api.etherscan.io/api'
    base_params = {
        'module': 'account',
        'action': 'balance',
        'address': address,
        'tag': 'latest'
    }
    
    try:
        params = create_params(base_params, api_key)
        response = requests.get(api_url, params=cast(Dict[str, str], params))
        response.raise_for_status()
        
        data = cast(EtherscanResponse, response.json())
        if data['status'] == '1':
            balance_wei = Decimal(str(data['result']))
            return balance_wei / Decimal('1000000000000000000')  # Convert Wei to ETH
        else:
            logger.error(f"Etherscan API error: {data['message']}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error checking balance: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error checking balance: {str(e)}")
        return None

def format_transaction(tx: Transaction) -> None:
    """
    Log formatted transaction information.
    
    Args:
        tx: Transaction data to format and log
    """
    timestamp = datetime.fromtimestamp(int(tx['timeStamp']))
    value_eth = Decimal(tx['value']) / Decimal('1000000000000000000')
    status = 'Success' if tx['txreceipt_status'] == '1' else 'Failed'
    
    logger.info(f"\nTransaction at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}:")
    logger.info(f"From: {tx['from_addr']}")
    logger.info(f"To: {tx['to']}")
    logger.info(f"Value: {value_eth:.6f} ETH")
    logger.info(f"Hash: {tx['hash']}")
    logger.info(f"Status: {status}")

def main() -> None:
    """Main function to check Ethereum address transactions and balance."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get configuration from environment
        api_key = get_etherscan_api_key()
        address = os.getenv('ETH_ADDRESS', '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801')
        
        # Get and display transactions
        logger.info(f"Checking latest transactions for {address}...")
        transactions = get_transactions(address, api_key)
        
        if transactions:
            for tx in transactions:
                format_transaction(tx)
        
        # Get and display balance
        balance = get_balance(address, api_key)
        if balance is not None:
            logger.info(f"\nCurrent balance: {balance:.6f} ETH")
            
    except ValueError as e:
        logger.error(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
