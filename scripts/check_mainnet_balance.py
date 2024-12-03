"""
Check mainnet wallet balance and gas prices
"""
from web3 import Web3
from web3.types import Wei, ChecksumAddress
from dotenv import load_dotenv
import os
from typing import Dict, Optional, TypedDict, cast, Tuple
from decimal import Decimal

from configs.logging_config import get_logger

logger = get_logger(__name__)

class DeploymentCost(TypedDict):
    """Type definition for deployment cost information."""
    gas_estimate: int
    eth_cost: Decimal

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

def get_deployment_estimates() -> Dict[str, int]:
    """
    Get estimated gas costs for contract deployments.
    
    Returns:
        Dictionary of contract names to estimated gas costs
    """
    return {
        'PriceFeedIntegration': 1000000,
        'ArbitrageBot': 2000000,
        'Setup & Config': 500000
    }

def wei_to_eth(w3: Web3, wei_amount: Wei) -> Decimal:
    """
    Convert Wei to ETH as Decimal.
    
    Args:
        w3: Web3 instance
        wei_amount: Amount in Wei
        
    Returns:
        Amount in ETH as Decimal
    """
    return Decimal(str(w3.from_wei(wei_amount, 'ether')))

def calculate_deployment_costs(
    w3: Web3,
    gas_price: Wei,
    estimates: Dict[str, int]
) -> Dict[str, DeploymentCost]:
    """
    Calculate deployment costs in ETH based on current gas price.
    
    Args:
        w3: Web3 instance
        gas_price: Current gas price in Wei
        estimates: Dictionary of contract names to estimated gas costs
        
    Returns:
        Dictionary of contract names to deployment costs
    """
    costs: Dict[str, DeploymentCost] = {}
    for contract, gas in estimates.items():
        eth_cost = wei_to_eth(w3, Wei(gas * gas_price))
        costs[contract] = {
            'gas_estimate': gas,
            'eth_cost': eth_cost
        }
    return costs

def check_balance_sufficiency(
    current_balance_eth: Decimal,
    total_cost: Decimal,
    buffer_percent: Decimal = Decimal('0.2')
) -> Tuple[bool, Optional[Decimal]]:
    """
    Check if balance is sufficient for deployment with buffer.
    
    Args:
        current_balance_eth: Current balance in ETH
        total_cost: Total deployment cost in ETH
        buffer_percent: Additional buffer as decimal percentage (default 0.2 for 20%)
        
    Returns:
        Tuple of (is_sufficient, eth_needed_if_insufficient)
    """
    required = total_cost * (Decimal('1') + buffer_percent)
    
    if current_balance_eth >= required:
        return True, None
    else:
        needed = required - current_balance_eth
        return False, needed

def main() -> None:
    """Main function to check mainnet balance and deployment costs."""
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
            
        # Connect to mainnet
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            logger.error("Failed to connect to mainnet")
            return
            
        logger.info(f"Connected to mainnet: {w3.is_connected()}")
        
        # Get deployment wallet address
        account = w3.eth.account.from_key(private_key)
        logger.info("\nDeployment Wallet:")
        logger.info(f"Address: {account.address}")
        
        # Check balance
        balance = w3.eth.get_balance(account.address)
        balance_eth = wei_to_eth(w3, balance)
        logger.info(f"Balance: {balance_eth} ETH")
        
        # Get current gas prices
        gas_price = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')
        logger.info(f"\nCurrent Gas Price: {gas_price_gwei} Gwei")
        
        # Calculate deployment costs
        estimates = get_deployment_estimates()
        costs = calculate_deployment_costs(w3, gas_price, estimates)
        
        # Display costs
        logger.info("\nEstimated deployment costs:")
        total_cost = Decimal('0')
        for contract, cost_info in costs.items():
            total_cost += cost_info['eth_cost']
            logger.info(f"{contract}: {cost_info['eth_cost']:.4f} ETH")
        
        logger.info(f"Total estimated cost: {total_cost:.4f} ETH")
        
        # Check if we have enough
        is_sufficient, eth_needed = check_balance_sufficiency(balance_eth, total_cost)
        
        if is_sufficient:
            logger.info("\n✓ Sufficient balance for deployment")
        else:
            logger.warning("\n✗ Insufficient balance for deployment")
            if eth_needed is not None:
                logger.warning(f"Need {eth_needed:.4f} more ETH")
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
