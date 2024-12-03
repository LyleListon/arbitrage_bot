"""
Check mainnet readiness and deployment requirements
"""
import os
from web3 import Web3
from web3.exceptions import Web3Exception
from dotenv import load_dotenv
import json
from typing import Dict, List, TypedDict, Optional, Any, Literal, cast, Union, Iterator, TypeVar, NamedTuple
from decimal import Decimal
from datetime import datetime
import re

from configs.logging_config import get_logger

logger = get_logger(__name__)

# Type definitions
CategoryType = Literal['Contracts', 'ABIs', 'Scripts']
CATEGORIES: List[CategoryType] = ['Contracts', 'ABIs', 'Scripts']

class EnvVarStatus(TypedDict):
    """Type definition for environment variable status."""
    present: bool
    value: str
    valid: bool
    error: Optional[str]

class FileStatus(TypedDict):
    """Type definition for file status."""
    exists: bool
    size: Optional[int]
    verified: bool

class CategoryFiles(TypedDict):
    """Type definition for category files."""
    Contracts: Dict[str, FileStatus]
    ABIs: Dict[str, FileStatus]
    Scripts: Dict[str, FileStatus]

class NetworkStatus(TypedDict):
    """Type definition for network status."""
    rpc: bool

class GasStatus(TypedDict):
    """Type definition for gas status."""
    current: Decimal
    base_fee: Decimal

class EnvResults(TypedDict):
    """Type definition for environment check results."""
    environment: Dict[str, Dict[str, EnvVarStatus]]
    files: CategoryFiles
    network: NetworkStatus
    gas: GasStatus
    timestamp: str
    recommendations: List[str]

def validate_env_var(name: str, value: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validate environment variable value.
    
    Args:
        name: Variable name
        value: Variable value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, "Value not set"
        
    if name.endswith('_ADDRESS'):
        # Validate Ethereum address
        if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
            return False, "Invalid Ethereum address format"
    elif name.endswith('_URL'):
        # Validate URL format
        if not value.startswith(('http://', 'https://')):
            return False, "Invalid URL format"
    elif name.endswith('_ENABLED'):
        # Validate boolean value
        if value.lower() not in ('true', 'false'):
            return False, "Must be 'true' or 'false'"
    elif name.startswith(('MAX_', 'MIN_')):
        # Validate numeric value
        try:
            float(value)
        except ValueError:
            return False, "Must be a numeric value"
            
    return True, None

def get_required_vars() -> Dict[str, List[str]]:
    """Get the list of required environment variables by category."""
    return {
        'Network': [
            'MAINNET_RPC_URL'
        ],
        'Contracts': [
            'WETH_ADDRESS',
            'USDC_ADDRESS',
            'UNISWAP_V2_ROUTER'
        ],
        'Price_Feeds': [
            'ETH_USD_PRICE_FEED',
            'USDC_USD_PRICE_FEED'
        ],
        'Configuration': [
            'MAX_TRADE_SIZE',
            'MIN_PROFIT_THRESHOLD',
            'MAX_SLIPPAGE',
            'MAX_GAS_PRICE_GWEI'
        ],
        'Safety': [
            'POSITION_SIZING_ENABLED',
            'DYNAMIC_GAS_PRICING',
            'MEV_PROTECTION_ENABLED',
            'SLIPPAGE_PROTECTION_ENABLED'
        ]
    }

def get_required_files() -> Dict[CategoryType, List[str]]:
    """Get the list of required files by category."""
    return {
        'Contracts': [
            'contracts/ArbitrageBot.sol',
            'contracts/PriceFeedIntegration.sol'
        ],
        'ABIs': [
            'abi/ArbitrageBot.json',
            'abi/PriceFeedIntegration.json'
        ],
        'Scripts': [
            'scripts/deploy_mainnet.py',
            'scripts/verify_deployment.py',
            'dashboard/app.py'
        ]
    }

def create_env_var_status(var_name: str) -> EnvVarStatus:
    """Create an environment variable status object."""
    value = os.getenv(var_name)
    is_valid, error = validate_env_var(var_name, value) if value else (False, "Not set")
    return EnvVarStatus(
        present=value is not None,
        value=value if value else 'Not set',
        valid=is_valid,
        error=error
    )

def check_environment() -> Dict[str, Dict[str, EnvVarStatus]]:
    """
    Check environment variables and configuration.
    
    Returns:
        Dictionary containing status of all required environment variables
    """
    load_dotenv('.env.mainnet')
    
    required_vars = get_required_vars()
    results: Dict[str, Dict[str, EnvVarStatus]] = {}
    
    for category, vars_list in required_vars.items():
        results[category] = {}
        for var in vars_list:
            results[category][var] = create_env_var_status(var)
    
    return results

def get_contract_size(file_path: str) -> Optional[int]:
    """Get contract file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None

def check_single_file(file_path: str) -> FileStatus:
    """
    Check a single file's status.
    
    Args:
        file_path: Path to the file
        
    Returns:
        FileStatus containing the file's status
    """
    exists = os.path.exists(file_path)
    size = get_contract_size(file_path) if exists else None
    verified = exists and size is not None and size > 0
    return FileStatus(
        exists=exists,
        size=size,
        verified=verified
    )

def check_files_in_category(files: List[str]) -> Dict[str, FileStatus]:
    """
    Check files in a category.
    
    Args:
        files: List of files to check
        
    Returns:
        Dictionary containing status of files
    """
    file_statuses: Dict[str, FileStatus] = {}
    
    for file in files:
        file_status = check_single_file(file)
        file_statuses[file] = file_status
        
        if not file_status['exists']:
            logger.warning(f"Required file missing: {file}")
        elif not file_status['verified']:
            logger.warning(f"File verification failed: {file}")
            
    return file_statuses

def check_contract_files() -> CategoryFiles:
    """
    Check required contract files.
    
    Returns:
        Dictionary containing status of all required files
    """
    required_files = get_required_files()
    
    contracts = check_files_in_category(required_files['Contracts'])
    abis = check_files_in_category(required_files['ABIs'])
    scripts = check_files_in_category(required_files['Scripts'])
    
    return CategoryFiles(
        Contracts=contracts,
        ABIs=abis,
        Scripts=scripts
    )

def check_network_connection() -> NetworkStatus:
    """Check network connections."""
    try:
        rpc_url = os.getenv('MAINNET_RPC_URL')
        if not rpc_url:
            return NetworkStatus(rpc=False)
            
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        return NetworkStatus(rpc=w3.is_connected())
    except Exception as e:
        logger.error(f"Network connection check error: {str(e)}")
        return NetworkStatus(rpc=False)

def check_gas_prices(w3: Optional[Web3] = None) -> GasStatus:
    """Check current gas prices."""
    try:
        if not w3:
            rpc_url = os.getenv('MAINNET_RPC_URL')
            if not rpc_url:
                return GasStatus(current=Decimal('0'), base_fee=Decimal('0'))
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
        if not w3.is_connected():
            return GasStatus(current=Decimal('0'), base_fee=Decimal('0'))
            
        gas_price = w3.eth.gas_price
        block = w3.eth.get_block('latest')
        base_fee = int(block['baseFeePerGas'])
        
        return GasStatus(
            current=Decimal(str(w3.from_wei(gas_price, 'gwei'))),
            base_fee=Decimal(str(w3.from_wei(base_fee, 'gwei')))
        )
    except Exception as e:
        logger.error(f"Gas price check error: {str(e)}")
        return GasStatus(current=Decimal('0'), base_fee=Decimal('0'))

def save_results(results: EnvResults) -> None:
    """
    Save readiness check results to file.
    
    Args:
        results: Results of readiness checks
    """
    try:
        with open('mainnet_readiness.json', 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("Readiness results saved to mainnet_readiness.json")
    except Exception as e:
        logger.error(f"Failed to save readiness results: {str(e)}")

def get_recommendations() -> List[str]:
    """Get the list of deployment recommendations."""
    return [
        'Review all configuration values',
        'Ensure price feeds are correct',
        'Verify contract addresses',
        'Check gas prices before deployment',
        'Have monitoring ready',
        'Test emergency procedures',
        'Verify network stability',
        'Check contract sizes',
        'Review safety parameters'
    ]

def check_env_readiness(env_results: Dict[str, Dict[str, EnvVarStatus]]) -> bool:
    """Check if environment variables are ready."""
    return all(
        status['present'] and status['valid']
        for category in env_results.values()
        for status in category.values()
    )

def check_files_readiness(file_results: CategoryFiles) -> bool:
    """Check if files are ready."""
    return all(
        status['verified']
        for category in CATEGORIES
        for status in file_results[category].values()
    )

def check_readiness() -> bool:
    """
    Check if system is ready for deployment.
    
    Returns:
        True if system is ready, False otherwise
    """
    logger.info("\n🔍 Checking Mainnet Deployment Readiness")
    
    # Check environment
    logger.info("\nChecking Environment Variables...")
    env_results = check_environment()
    
    for category, vars_dict in env_results.items():
        logger.info(f"\n{category}:")
        for var, status in vars_dict.items():
            status_symbol = '✓' if status['present'] and status['valid'] else '✗'
            logger.info(f"{status_symbol} {var}")
            if not status['present']:
                logger.warning(f"Missing environment variable: {var}")
            elif not status['valid']:
                logger.warning(f"Invalid value for {var}: {status['error']}")
    
    # Check files
    logger.info("\nChecking Required Files...")
    file_results = check_contract_files()
    
    for category in CATEGORIES:
        logger.info(f"\n{category}:")
        for file, status in file_results[category].items():
            status_symbol = '✓' if status['verified'] else '✗'
            logger.info(f"{status_symbol} {file}")
            if status['size'] is not None:
                logger.info(f"  Size: {status['size']} bytes")
    
    # Check network connections
    logger.info("\nChecking Network Connection...")
    network_status = check_network_connection()
    logger.info(f"RPC Connection: {'✓' if network_status['rpc'] else '✗'}")
    
    # Check gas prices
    logger.info("\nChecking Gas Prices...")
    gas_prices = check_gas_prices()
    logger.info(f"Current Gas Price: {gas_prices['current']:.2f} Gwei")
    logger.info(f"Base Fee: {gas_prices['base_fee']:.2f} Gwei")
    
    # Prepare results
    recommendations = get_recommendations()
    
    results = EnvResults(
        timestamp=datetime.now().isoformat(),
        environment=env_results,
        files=file_results,
        network=network_status,
        gas=gas_prices,
        recommendations=recommendations
    )
    
    save_results(results)
    
    # Check overall readiness
    env_ready = check_env_readiness(env_results)
    files_ready = check_files_readiness(file_results)
    network_ready = network_status['rpc']
    gas_ready = gas_prices['current'] > Decimal('0') and gas_prices['base_fee'] > Decimal('0')
    
    system_ready = env_ready and files_ready and network_ready and gas_ready
    
    if system_ready:
        logger.info("\n✓ System ready for mainnet deployment")
        logger.info("\nNext steps:")
        for i, step in enumerate(recommendations, 1):
            logger.info(f"{i}. {step}")
    else:
        logger.error("\n✗ System not ready for deployment")
        logger.error("Please fix the issues marked with ✗ above")
    
    return system_ready

def main() -> None:
    """Main function to check mainnet deployment readiness."""
    try:
        check_readiness()
    except Exception as e:
        logger.error(f"Unexpected error during readiness check: {str(e)}")

if __name__ == '__main__':
    main()
