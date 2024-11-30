"""
Check ownership and deployment information for smart contracts
"""
from web3 import Web3
from web3.contract import Contract
from web3.types import ChecksumAddress
from web3.contract.contract import ContractFunction
from dotenv import load_dotenv
import json
from typing import Dict, Any, Optional, TypedDict, List, Union, cast, NoReturn
import os
from datetime import datetime

from configs.logging_config import get_logger

logger = get_logger(__name__)

# Type alias for contract ABI
ContractABI = List[Dict[str, Any]]

class DeploymentInfo(TypedDict):
    """Type definition for deployment information."""
    deployer: str
    timestamp: str
    transaction_hash: str

def load_contract_abi(name: str) -> Optional[ContractABI]:
    """
    Load contract ABI from file.
    
    Args:
        name: Name of the contract
        
    Returns:
        Contract ABI if successful, None if failed
    """
    try:
        with open(f'abi/{name}.json', 'r') as f:
            return cast(ContractABI, json.load(f))
    except FileNotFoundError:
        logger.error(f"ABI file not found: abi/{name}.json")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in ABI file: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading ABI: {str(e)}")
        return None

def load_contract(w3: Web3, name: str, address: ChecksumAddress) -> Optional[Contract]:
    """
    Load contract ABI and create contract instance.
    
    Args:
        w3: Web3 instance
        name: Name of the contract
        address: Contract address
        
    Returns:
        Contract instance if successful, None if failed
    """
    abi = load_contract_abi(name)
    if not abi:
        return None
        
    try:
        return w3.eth.contract(address=address, abi=abi)
    except Exception as e:
        logger.error(f"Error creating contract instance: {str(e)}")
        return None

def check_contract_owner(contract: Contract, our_address: ChecksumAddress) -> Optional[ChecksumAddress]:
    """
    Check the owner of a contract.
    
    Args:
        contract: Contract instance
        our_address: Our Ethereum address
        
    Returns:
        Owner address if successful, None if failed
    """
    try:
        owner_func = cast(ContractFunction, contract.functions.owner())
        owner: str = owner_func.call()  # type: ignore
        owner_address = Web3.to_checksum_address(owner)
        logger.info(f"Contract owner: {owner_address}")
        is_owner = owner_address.lower() == our_address.lower()
        logger.info(f"Are we the owner? {'✓' if is_owner else '✗'}")
        return owner_address
    except Exception as e:
        logger.error(f"Error checking owner: {str(e)}")
        return None

def load_deployment_info(contract_name: str, network: str) -> Optional[DeploymentInfo]:
    """
    Load deployment information from file.
    
    Args:
        contract_name: Name of the contract
        network: Network name (e.g., 'holesky')
        
    Returns:
        Deployment information if successful, None if failed
    """
    try:
        with open(f'deployments/{contract_name}_{network}.json', 'r') as f:
            data = json.load(f)
            # Validate the required fields are present
            if not all(k in data for k in ('deployer', 'timestamp', 'transaction_hash')):
                logger.error("Missing required fields in deployment info")
                return None
            return DeploymentInfo(
                deployer=str(data['deployer']),
                timestamp=str(data['timestamp']),
                transaction_hash=str(data['transaction_hash'])
            )
    except FileNotFoundError:
        logger.error(f"Deployment file not found: deployments/{contract_name}_{network}.json")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in deployment file: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading deployment info: {str(e)}")
        return None

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

def main() -> None:
    """Main function to check contract ownership and deployment information."""
    try:
        # Load environment and connect to Holesky
        load_dotenv('.env.holesky')
        
        # Get required environment variables
        try:
            rpc_url = get_env_var('HOLESKY_RPC_URL')
            private_key = get_env_var('HOLESKY_PRIVATE_KEY')
            mock_feed_address = get_env_var('HOLESKY_PRICE_FEED_ADDRESS')
        except ValueError as e:
            logger.error(str(e))
            return
            
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            logger.error("Failed to connect to Holesky network")
            return
            
        logger.info(f"Connected to Holesky: {w3.is_connected()}")
        
        # Get our address
        account = w3.eth.account.from_key(private_key)
        our_address = account.address
        logger.info(f"\nOur address: {our_address}")
        
        # Load mock feed contract
        mock_feed_address_checksum = Web3.to_checksum_address(mock_feed_address)
        logger.info(f"MockPriceFeed address: {mock_feed_address_checksum}")
        
        mock_feed = load_contract(w3, 'MockPriceFeed', mock_feed_address_checksum)
        if not mock_feed:
            return
        
        # Check owner
        owner = check_contract_owner(mock_feed, our_address)
        if not owner:
            return
        
        # Check deployment info
        deployment = load_deployment_info('MockPriceFeed', 'holesky')
        if deployment:
            logger.info("\nDeployment Info:")
            logger.info(f"Deployer: {deployment['deployer']}")
            logger.info(f"Timestamp: {deployment['timestamp']}")
            logger.info(f"Transaction: {deployment['transaction_hash']}")
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")

if __name__ == '__main__':
    main()
