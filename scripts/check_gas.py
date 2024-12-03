"""
Check gas prices and estimate deployment costs on Ethereum mainnet
"""
from web3 import Web3
from web3.exceptions import Web3Exception
from web3.types import Wei, ChecksumAddress, BlockData
from typing import Dict, Optional, Tuple, Union, List, TypedDict, cast
from decimal import Decimal
from dotenv import load_dotenv
import os
import time
from statistics import mean, median

from configs.logging_config import get_logger

logger = get_logger(__name__)

class GasStats(TypedDict):
    """Type definition for gas price statistics."""
    min: Decimal
    max: Decimal
    avg: Decimal
    median: Decimal

class DeploymentCosts(TypedDict):
    """Type definition for deployment costs."""
    costs: Dict[str, Decimal]
    total: Decimal

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

def format_gas_value(w3: Web3, value: Wei) -> str:
    """
    Format Wei value to Gwei string with proper precision.
    
    Args:
        w3: Web3 instance
        value: Value in Wei
        
    Returns:
        Formatted string in Gwei
    """
    gwei_value = Decimal(str(w3.from_wei(value, 'gwei')))
    return f"{gwei_value:.2f} Gwei"

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

def get_gas_info(w3: Web3) -> Optional[Tuple[Wei, int, BlockData]]:
    """
    Get current gas price and block information.
    
    Args:
        w3: Web3 instance to use
        
    Returns:
        Tuple of (gas_price, base_fee, block) if successful, None if failed
    """
    try:
        gas_price = w3.eth.gas_price
        block = w3.eth.get_block('latest')
        # Explicitly convert baseFeePerGas to int to satisfy type checker
        base_fee = int(block['baseFeePerGas'])
        return gas_price, base_fee, block
    except Web3Exception as e:
        logger.error(f"Web3 error getting gas info: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting gas info: {str(e)}")
        return None

def get_estimated_gas_limits() -> Dict[str, int]:
    """
    Get estimated gas limits from environment or use defaults.
    
    Returns:
        Dictionary of contract names to estimated gas limits
    """
    try:
        return {
            'PriceFeedIntegration': int(get_env_var('PRICE_FEED_GAS_LIMIT')),
            'ArbitrageBot': int(get_env_var('ARBITRAGE_BOT_GAS_LIMIT')),
            'Setup & Config': int(get_env_var('SETUP_GAS_LIMIT'))
        }
    except (ValueError, KeyError):
        logger.warning("Using default gas limits")
        return {
            'PriceFeedIntegration': 1000000,
            'ArbitrageBot': 2000000,
            'Setup & Config': 500000
        }

def calculate_deployment_costs(w3: Web3, gas_price: Wei) -> DeploymentCosts:
    """
    Calculate estimated deployment costs for contracts.
    
    Args:
        w3: Web3 instance to use
        gas_price: Current gas price
        
    Returns:
        Dictionary containing costs per contract and total cost
    """
    estimated_gas = get_estimated_gas_limits()
    
    costs: Dict[str, Decimal] = {}
    total = Decimal('0')
    
    for contract, gas in estimated_gas.items():
        cost = Decimal(str(w3.from_wei(gas * gas_price, 'ether')))
        costs[contract] = cost
        total += cost
    
    return {
        'costs': costs,
        'total': total
    }

def calculate_gas_stats(gas_prices: List[Wei]) -> GasStats:
    """
    Calculate gas price statistics.
    
    Args:
        gas_prices: List of gas prices in Wei
        
    Returns:
        Statistics about gas prices
    """
    if not gas_prices:
        zero = Decimal('0')
        return {
            'min': zero,
            'max': zero,
            'avg': zero,
            'median': zero
        }
        
    gwei_prices = [Decimal(str(p)) for p in gas_prices]
    return {
        'min': min(gwei_prices),
        'max': max(gwei_prices),
        'avg': Decimal(str(mean(gwei_prices))),
        'median': Decimal(str(median(gwei_prices)))
    }

def check_wallet_balance(w3: Web3, private_key: str) -> Optional[Tuple[Wei, ChecksumAddress]]:
    """
    Check the balance of the deployment wallet.
    
    Args:
        w3: Web3 instance to use
        private_key: Private key of the wallet
        
    Returns:
        Tuple of (balance, address) if successful, None if failed
    """
    try:
        account = w3.eth.account.from_key(private_key)
        balance = w3.eth.get_balance(account.address)
        return balance, account.address
    except Exception as e:
        logger.error(f"Error checking wallet balance: {str(e)}")
        return None

def main() -> None:
    """Main function to check gas prices and estimate deployment costs."""
    try:
        # Load mainnet configuration
        load_dotenv('.env.mainnet')
        
        # Get required environment variables
        try:
            rpc_url = get_env_var('MAINNET_RPC_URL')
            private_key = get_env_var('MAINNET_PRIVATE_KEY')
        except ValueError as e:
            logger.error(str(e))
            return
            
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            logger.error("Failed to connect to mainnet")
            return
            
        logger.info(f"Connected to mainnet: {w3.is_connected()}")
        
        # Track gas prices across iterations
        gas_prices: List[Wei] = []
        latest_costs: Optional[DeploymentCosts] = None
        
        # Check gas prices multiple times
        for i in range(3):
            logger.info("\nChecking gas prices...")
            gas_info = get_gas_info(w3)
            
            if not gas_info:
                continue
                
            gas_price, base_fee, block = gas_info
            gas_prices.append(gas_price)
            
            logger.info(f"Block {block['number']}:")
            logger.info(f"Base Fee: {format_gas_value(w3, Wei(base_fee))}")
            logger.info(f"Gas Price: {format_gas_value(w3, gas_price)}")
            
            # Calculate deployment costs
            latest_costs = calculate_deployment_costs(w3, gas_price)
            
            logger.info("\nEstimated deployment costs:")
            for contract, cost in latest_costs['costs'].items():
                logger.info(f"{contract}: {cost:.4f} ETH")
            logger.info(f"Total estimated cost: {latest_costs['total']:.4f} ETH")
            
            if i < 2:  # Don't sleep on last iteration
                logger.info("Waiting 15 seconds for next check...")
                time.sleep(15)
        
        # Log gas price statistics
        stats = calculate_gas_stats(gas_prices)
        logger.info("\nGas Price Statistics:")
        logger.info(f"Minimum: {stats['min']:.2f} Gwei")
        logger.info(f"Maximum: {stats['max']:.2f} Gwei")
        logger.info(f"Average: {stats['avg']:.2f} Gwei")
        logger.info(f"Median: {stats['median']:.2f} Gwei")
        
        # Check wallet balance
        wallet_info = check_wallet_balance(w3, private_key)
        if wallet_info and latest_costs:
            balance, address = wallet_info
            logger.info(f"\nDeployment wallet balance: {format_eth_value(w3, balance)}")
            logger.info(f"Address: {address}")
            
            # Check if we have enough balance with buffer
            buffer_percent = Decimal('0.1')  # 10% buffer
            required = w3.to_wei(latest_costs['total'] * (Decimal('1') + buffer_percent), 'ether')
            
            if balance < required:
                needed = w3.from_wei(required - balance, 'ether')
                logger.warning(f"Insufficient balance for deployment (including {buffer_percent*100}% buffer)")
                logger.warning(f"Need {needed:.4f} more ETH")
            else:
                logger.info("Sufficient balance for deployment")
                
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
