"""
Configuration loader for arbitrage bot dashboard

@CONTEXT: Handles loading and validation of configuration
@LAST_POINT: 2024-01-31 - Added network-specific configuration handling
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from dashboard.data_providers.base_provider import PairConfig, ExchangeConfig

logger = logging.getLogger(__name__)


@dataclass
class NetworkConfig:
    """Network configuration settings"""
    name: str
    chain_id: int
    rpc_url: str
    wss_url: Optional[str] = None


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings"""
    max_price_deviation: float = 1.0
    update_interval: int = 5
    alert_threshold: float = 5.0
    log_level: str = "INFO"
    health_check_interval: int = 30
    max_block_delay: int = 60
    min_peer_count: int = 3


class ConfigLoader:
    """Configuration loader with network-specific handling"""
    
    def __init__(self, network: str = "development"):
        """
        Initialize config loader
        
        Args:
            network: Network to load configuration for (development/sepolia/mainnet)
        """
        self.network = network
        self.config: Dict[str, Any] = {}
        self.env_file = f".env.{network}"
        self._load_environment()
        self._load_default_config()
    
    def _load_environment(self) -> None:
        """Load environment variables for specific network"""
        env_path = os.path.join("dashboard", self.env_file)
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
        else:
            logger.warning(f"Environment file not found: {env_path}")
    
    def _load_default_config(self) -> None:
        """Load default configuration"""
        self.config = {
            'network': {
                'name': self.network,
                'chain_id': 31337,  # Default to Hardhat
                'rpc_url': "http://127.0.0.1:8545"
            },
            'performance': {
                'cache_duration': 5,
                'max_pairs': 100,
                'max_exchanges': 10
            },
            'monitoring': {
                'max_price_deviation': 1.0,
                'update_interval': 5,
                'alert_threshold': 5.0,
                'log_level': 'INFO',
                'health_check_interval': 30,
                'max_block_delay': 60,
                'min_peer_count': 3
            }
        }
    
    def _substitute_env_vars(self, value: str) -> str:
        """Substitute environment variables in string"""
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            env_value = os.getenv(env_var)
            if env_value is None:
                logger.warning(f"Environment variable not found: {env_var}")
                return value
            return env_value
        return value
    
    def _process_config_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively process config values for env var substitution"""
        processed = {}
        for key, value in config.items():
            if isinstance(value, dict):
                processed[key] = self._process_config_values(value)
            elif isinstance(value, list):
                processed[key] = [self._substitute_env_vars(v) for v in value]
            else:
                processed[key] = self._substitute_env_vars(value)
        return processed
    
    def load_config(self) -> Dict[str, Any]:
        """Load network-specific configuration"""
        try:
            config_path = os.path.join("dashboard", "config", f"trading_config.{self.network}.yaml")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    # Process environment variables
                    processed_config = self._process_config_values(file_config)
                    self.config.update(processed_config)
                logger.info(f"Loaded configuration for network: {self.network}")
            else:
                logger.warning(f"Config file not found: {config_path}, using defaults")
            
            return self.config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.config
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        try:
            # Check required sections
            required_sections = ['network', 'performance', 'monitoring', 'pairs', 'exchanges']
            for section in required_sections:
                if section not in self.config:
                    logger.error(f"Missing required section: {section}")
                    return False
            
            # Validate network settings
            net = self.config['network']
            if not all(net.get(k) for k in ['name', 'chain_id', 'rpc_url']):
                logger.error("Invalid network settings")
                return False
            
            # Validate performance settings
            perf = self.config['performance']
            if not all(isinstance(perf.get(k), (int, float)) for k in ['cache_duration', 'max_pairs', 'max_exchanges']):
                logger.error("Invalid performance settings")
                return False
            
            # Validate monitoring settings
            mon = self.config['monitoring']
            if not all(isinstance(mon.get(k), (int, float, str)) for k in ['max_price_deviation', 'update_interval', 'alert_threshold', 'log_level']):
                logger.error("Invalid monitoring settings")
                return False
            
            # Validate pairs
            for pair_id, pair_config in self.config['pairs'].items():
                if not self._validate_pair_config(pair_id, pair_config):
                    return False
            
            # Validate exchanges
            for exchange_id, exchange_config in self.config['exchanges'].items():
                if not self._validate_exchange_config(exchange_id, exchange_config):
                    return False
            
            logger.info("Configuration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return False
    
    def _validate_pair_config(self, pair_id: str, config: Dict[str, Any]) -> bool:
        """Validate trading pair configuration"""
        required_fields = [
            'base_token', 'quote_token', 'chainlink_feed', 'decimals',
            'min_profit_threshold', 'max_slippage'
        ]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field '{field}' in pair config: {pair_id}")
                return False
            
            # Validate addresses
            if field in ['base_token', 'quote_token', 'chainlink_feed']:
                if not self._is_valid_address(config[field]):
                    logger.error(f"Invalid address for {field} in pair config: {pair_id}")
                    return False
        
        return True
    
    def _validate_exchange_config(self, exchange_id: str, config: Dict[str, Any]) -> bool:
        """Validate exchange configuration"""
        required_fields = [
            'name', 'router', 'factory', 'supported_pairs',
            'fee_structure', 'min_order_size', 'max_order_size'
        ]
        
        for field in required_fields:
            if field not in config:
                logger.error(f"Missing required field '{field}' in exchange config: {exchange_id}")
                return False
            
            # Validate addresses
            if field in ['router', 'factory']:
                if not self._is_valid_address(config[field]):
                    logger.error(f"Invalid address for {field} in exchange config: {exchange_id}")
                    return False
        
        return True
    
    def _is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if isinstance(address, str) and address.startswith("${"):
            return True  # Environment variable placeholder
        return isinstance(address, str) and address.startswith("0x") and len(address) == 42
    
    def get_network_config(self) -> NetworkConfig:
        """Get network configuration"""
        net = self.config.get('network', {})
        return NetworkConfig(
            name=net.get('name', 'development'),
            chain_id=net.get('chain_id', 31337),
            rpc_url=net.get('rpc_url', 'http://127.0.0.1:8545'),
            wss_url=net.get('wss_url')
        )
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        mon = self.config.get('monitoring', {})
        return MonitoringConfig(
            max_price_deviation=mon.get('max_price_deviation', 1.0),
            update_interval=mon.get('update_interval', 5),
            alert_threshold=mon.get('alert_threshold', 5.0),
            log_level=mon.get('log_level', 'INFO'),
            health_check_interval=mon.get('health_check_interval', 30),
            max_block_delay=mon.get('max_block_delay', 60),
            min_peer_count=mon.get('min_peer_count', 3)
        )
    
    def get_pair_configs(self) -> Dict[str, PairConfig]:
        """Get trading pair configurations"""
        pairs = {}
        for pair_id, config in self.config.get('pairs', {}).items():
            pairs[pair_id] = PairConfig(
                base_token=config['base_token'],
                quote_token=config['quote_token'],
                decimals=config['decimals'],
                min_profit_threshold=config['min_profit_threshold'],
                max_slippage=config['max_slippage'],
                min_liquidity=config.get('min_liquidity', 0.0),
                is_active=config.get('is_active', True)
            )
        return pairs
    
    def get_exchange_configs(self) -> Dict[str, ExchangeConfig]:
        """Get exchange configurations"""
        exchanges = {}
        for exchange_id, config in self.config.get('exchanges', {}).items():
            exchanges[exchange_id] = ExchangeConfig(
                name=config['name'],
                supported_pairs=config['supported_pairs'],
                fee_structure=config['fee_structure'],
                min_order_size=config['min_order_size'],
                max_order_size=config['max_order_size'],
                is_active=config.get('is_active', True)
            )
        return exchanges
