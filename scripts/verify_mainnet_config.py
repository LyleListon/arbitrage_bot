"""
Mainnet configuration verification script

@CONTEXT: Verify all mainnet settings before deployment
@LAST_POINT: 2024-01-31 - Initial safety checks
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any
from web3 import Web3
import yaml


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigVerificationError(Exception):
    """Custom exception for configuration verification failures"""
    pass


def load_config() -> Dict[str, Any]:
    """Load mainnet configuration"""
    try:
        config_path = Path('dashboard/config/trading_config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if config['network']['name'] != 'mainnet':
            raise ConfigVerificationError("Configuration not set for mainnet")
            
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise


def verify_network_connection(config: Dict[str, Any]) -> None:
    """Verify connection to Ethereum mainnet"""
    try:
        w3 = Web3(Web3.HTTPProvider(config['network']['rpc_url']))
        if not w3.is_connected():
            raise ConfigVerificationError("Cannot connect to Ethereum network")
            
        chain_id = w3.eth.chain_id
        if chain_id != 1:
            raise ConfigVerificationError(f"Wrong network: Expected mainnet (1), got {chain_id}")
            
        logger.info("Network connection verified: Ethereum mainnet")
    except Exception as e:
        logger.error(f"Network verification failed: {e}")
        raise


def verify_contract_addresses(config: Dict[str, Any]) -> None:
    """Verify all contract addresses are valid mainnet addresses"""
    try:
        # Verify registry addresses
        for name, addr in config['contracts'].items():
            if not Web3.is_address(addr):
                raise ConfigVerificationError(f"Invalid {name} address: {addr}")
        
        # Verify token addresses
        for pair in config['pairs'].values():
            if not Web3.is_address(pair['base_token']):
                raise ConfigVerificationError(f"Invalid base token address: {pair['base_token']}")
            if not Web3.is_address(pair['quote_token']):
                raise ConfigVerificationError(f"Invalid quote token address: {pair['quote_token']}")
            if not Web3.is_address(pair['chainlink_feed']):
                raise ConfigVerificationError(f"Invalid Chainlink feed address: {pair['chainlink_feed']}")
        
        # Verify exchange addresses
        for exchange in config['exchanges'].values():
            if not Web3.is_address(exchange['router']):
                raise ConfigVerificationError(f"Invalid router address: {exchange['router']}")
            if not Web3.is_address(exchange['factory']):
                raise ConfigVerificationError(f"Invalid factory address: {exchange['factory']}")
        
        logger.info("Contract addresses verified")
    except Exception as e:
        logger.error(f"Contract address verification failed: {e}")
        raise


def verify_price_feeds(config: Dict[str, Any]) -> None:
    """Verify Chainlink price feeds are responding"""
    try:
        w3 = Web3(Web3.HTTPProvider(config['network']['rpc_url']))
        
        # Load Chainlink ABI
        with open('dashboard/chainlink_abi.json', 'r') as f:
            chainlink_abi = json.load(f)
        
        for pair_id, pair_config in config['pairs'].items():
            feed = w3.eth.contract(
                address=pair_config['chainlink_feed'],
                abi=chainlink_abi
            )
            
            # Check feed is responding
            latest = feed.functions.latestRoundData().call()
            price = latest[1]
            timestamp = latest[3]
            
            if price <= 0:
                raise ConfigVerificationError(f"Invalid price from {pair_id} feed: {price}")
            
            if timestamp < (w3.eth.get_block('latest').timestamp - 3600):
                raise ConfigVerificationError(f"Stale price data for {pair_id}")
            
            logger.info(f"Price feed verified for {pair_id}")
    except Exception as e:
        logger.error(f"Price feed verification failed: {e}")
        raise


def verify_safety_parameters(config: Dict[str, Any]) -> None:
    """Verify safety parameters are properly set"""
    try:
        # Check performance parameters
        perf = config['performance']
        if perf['max_gas_price'] <= 0:
            raise ConfigVerificationError("Invalid max_gas_price")
        if perf['min_profit_threshold'] <= 0:
            raise ConfigVerificationError("Invalid min_profit_threshold")
        if perf['max_slippage'] <= 0:
            raise ConfigVerificationError("Invalid max_slippage")
        
        # Check monitoring parameters
        mon = config['monitoring']
        if mon['max_price_deviation'] <= 0:
            raise ConfigVerificationError("Invalid max_price_deviation")
        if mon['update_interval'] <= 0:
            raise ConfigVerificationError("Invalid update_interval")
        if mon['health_check_interval'] <= 0:
            raise ConfigVerificationError("Invalid health_check_interval")
        
        # Check trading parameters
        for pair in config['pairs'].values():
            if pair['min_liquidity'] <= 0:
                raise ConfigVerificationError("Invalid min_liquidity")
            if pair['max_slippage'] <= 0:
                raise ConfigVerificationError("Invalid pair max_slippage")
        
        logger.info("Safety parameters verified")
    except Exception as e:
        logger.error(f"Safety parameter verification failed: {e}")
        raise


def verify_exchange_config(config: Dict[str, Any]) -> None:
    """Verify exchange configuration"""
    try:
        for exchange_id, exchange in config['exchanges'].items():
            # Check fee structure
            for pair_id, fee in exchange['fee_structure'].items():
                if fee <= 0 or fee >= 1:
                    raise ConfigVerificationError(f"Invalid fee for {exchange_id} {pair_id}: {fee}")
            
            # Check order size limits
            for pair_id in exchange['supported_pairs']:
                min_size = exchange['min_order_size'][pair_id]
                max_size = exchange['max_order_size'][pair_id]
                if min_size <= 0:
                    raise ConfigVerificationError(f"Invalid min_order_size for {exchange_id} {pair_id}")
                if max_size <= min_size:
                    raise ConfigVerificationError("max_order_size must be greater than min_order_size")
        
        logger.info("Exchange configuration verified")
    except Exception as e:
        logger.error(f"Exchange configuration verification failed: {e}")
        raise


def verify_token_balances(config: Dict[str, Any]) -> None:
    """Verify token balances and allowances"""
    try:
        w3 = Web3(Web3.HTTPProvider(config['network']['rpc_url']))
        wallet = config.get('wallet_address')
        if not wallet:
            raise ConfigVerificationError("Wallet address not configured")
            
        # Load ERC20 ABI
        with open('abi/IERC20.json', 'r') as f:
            erc20_abi = json.load(f)
        
        # Check balances and allowances for each token
        for pair_id, pair_config in config['pairs'].items():
            for token_addr in [pair_config['base_token'], pair_config['quote_token']]:
                token = w3.eth.contract(address=token_addr, abi=erc20_abi)
                balance = token.functions.balanceOf(wallet).call()
                
                if balance <= 0:
                    logger.warning(f"No balance for token {token_addr} in pair {pair_id}")
                
                # Check allowances for each exchange
                for exchange in config['exchanges'].values():
                    allowance = token.functions.allowance(
                        wallet,
                        exchange['router']
                    ).call()
                    
                    if allowance <= 0:
                        logger.warning(
                            f"No allowance for token {token_addr} "
                            f"on exchange {exchange['name']}"
                        )
        
        logger.info("Token balances and allowances verified")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise


def verify_gas_estimates(config: Dict[str, Any]) -> None:
    """Verify gas estimates for typical operations"""
    try:
        w3 = Web3(Web3.HTTPProvider(config['network']['rpc_url']))
        wallet = config.get('wallet_address')
        if not wallet:
            raise ConfigVerificationError("Wallet address not configured")
            
        # Load router ABI
        with open('abi/IUniswapV2Router.json', 'r') as f:
            router_abi = json.load(f)
        
        # Check gas estimates for each exchange and pair
        for exchange_id, exchange in config['exchanges'].items():
            router = w3.eth.contract(
                address=exchange['router'],
                abi=router_abi
            )
            
            for pair_id, pair_config in config['pairs'].items():
                # Estimate gas for a minimal swap
                try:
                    min_amount = exchange['min_order_size'][pair_id]
                    amount_in = int(min_amount * (10 ** pair_config['decimals']))
                    
                    gas_estimate = router.functions.swapExactTokensForTokens(
                        amount_in,
                        0,  # Accept any amount of tokens
                        [pair_config['base_token'], pair_config['quote_token']],
                        wallet,
                        w3.eth.get_block('latest').timestamp + 1800  # 30 min deadline
                    ).estimate_gas({'from': wallet})
                    
                    # Check if gas estimate is reasonable
                    if gas_estimate > 500000:  # Arbitrary high gas limit
                        logger.warning(
                            f"High gas estimate for {exchange_id} {pair_id}: "
                            f"{gas_estimate} gas"
                        )
                    
                    logger.info(
                        f"Gas estimate for {exchange_id} {pair_id}: "
                        f"{gas_estimate} gas"
                    )
                    
                except Exception as e:
                    logger.warning(
                        f"Could not estimate gas for {exchange_id} {pair_id}: {str(e)}"
                    )
        
        logger.info("Gas estimates verified")
    except Exception as e:
        logger.error(f"Gas estimation failed: {e}")
        raise


def main() -> int:
    """Main verification routine"""
    try:
        logger.info("Starting mainnet configuration verification")
        
        # Load and verify configuration
        config = load_config()
        logger.info("Configuration loaded")
        
        # Run verifications
        verify_network_connection(config)
        verify_contract_addresses(config)
        verify_price_feeds(config)
        verify_safety_parameters(config)
        verify_exchange_config(config)
        verify_token_balances(config)
        verify_gas_estimates(config)
        
        logger.info("All verifications passed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
