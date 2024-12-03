"""
Check ETH balance across multiple RPC endpoints with fallback support
"""
from web3 import Web3
from web3.exceptions import Web3Exception
from web3.types import Wei, ChecksumAddress
from typing import List, Optional, Tuple, Dict, Any
from dotenv import load_dotenv
import os
from decimal import Decimal

from configs.logging_config import get_logger

logger = get_logger(__name__)

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

def check_balance(w3: Web3, address: ChecksumAddress) -> Optional[Tuple[Wei, int]]:
    """
    Check ETH balance and current block number for a given address using Web3 instance.
    
    Args:
        w3: Web3 instance to use
        address: The Ethereum address to check
        
    Returns:
        Tuple of (balance, block_number) if successful, None if failed
    """
    try:
        if not w3.is_connected():
            logger.warning("Web3 instance not connected")
            return None
            
        balance = w3.eth.get_balance(address)
        block_number = w3.eth.block_number
        return balance, block_number
        
    except Web3Exception as e:
        logger.error(f"Web3 error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return None

def get_web3(rpc_url: str) -> Optional[Web3]:
    """
    Create a Web3 instance for the given RPC URL.
    
    Args:
        rpc_url: The RPC endpoint URL
        
    Returns:
        Web3 instance if successful, None if failed
    """
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            logger.warning(f"Failed to connect to RPC: {rpc_url}")
            return None
        return w3
    except Exception as e:
        logger.error(f"Failed to create Web3 instance for {rpc_url}: {str(e)}")
        return None

def get_rpc_endpoints() -> List[str]:
    """
    Get list of RPC endpoints from environment or use defaults.
    
    Returns:
        List of RPC URLs
    """
    # Try to get RPC URLs from environment
    rpc_urls = []
    for i in range(1, 5):  # Check for RPC_URL_1 through RPC_URL_4
        url = os.getenv(f'RPC_URL_{i}')
        if url:
            rpc_urls.append(url)
    
    # If no RPC URLs found in environment, use defaults
    if not rpc_urls:
        logger.warning("No RPC URLs found in environment, using defaults")
        rpc_urls = [
            'https://eth-mainnet.g.alchemy.com/v2/kRXhWVt8YU_8LnGS20145F5uBDFbL_k0',
            'https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',  # Public Infura
            'https://rpc.ankr.com/eth',  # Public Ankr
            'https://cloudflare-eth.com'  # Cloudflare
        ]
    
    return rpc_urls

def main() -> None:
    """Main function to check ETH balance across multiple RPCs."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get address from environment or use default
        try:
            raw_address = os.getenv('ETH_ADDRESS', '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801')
            address = Web3.to_checksum_address(raw_address)
            logger.info(f"Checking balance for address: {address}")
        except ValueError as e:
            logger.error(f"Invalid Ethereum address: {str(e)}")
            return
        
        # Get RPC endpoints
        rpcs = get_rpc_endpoints()
        logger.info(f"Found {len(rpcs)} RPC endpoints to try")
        
        success = False
        for i, rpc in enumerate(rpcs, 1):
            logger.info(f"\nAttempting RPC {i}/{len(rpcs)}: {rpc}")
            w3 = get_web3(rpc)
            if not w3:
                continue
                
            result = check_balance(w3, address)
            if result:
                balance, block_number = result
                logger.info("Balance check successful!")
                logger.info(f"Balance: {format_eth_value(w3, balance)}")
                logger.info(f"Block Number: {block_number}")
                success = True
                break
            else:
                logger.warning(f"Failed to check balance with RPC {i}")
        
        if not success:
            logger.error("Failed to check balance with all available RPCs")
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
