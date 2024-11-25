import os
import json
from typing import Dict, Any, Optional, Union, TypedDict, cast, Literal, Type, TypeVar

# Literal types for network configurations
NetworkName = Literal['ethereum', 'binance_smart_chain', 'polygon']
NetworkType = Literal['mainnet', 'testnet']
EndpointPriority = Literal['primary', 'secondary', 'fallback']

T = TypeVar('T')

def safe_get(obj: Any, key: str, default: Optional[T] = None) -> Optional[T]:
    """
    Safely get a value from a dictionary-like object
    
    :param obj: Object to get value from
    :param key: Key to retrieve
    :param default: Default value if key not found
    :return: Retrieved value or default
    """
    try:
        return obj[key] if isinstance(obj, dict) else default
    except (TypeError, KeyError):
        return default

class NetworkEndpointConfig(TypedDict):
    """
    Type definition for network endpoint configuration
    """
    primary: str
    secondary: str
    fallback: str

class NetworkTypeConfig(TypedDict):
    """
    Type definition for network type configuration
    """
    mainnet: NetworkEndpointConfig
    testnet: NetworkEndpointConfig

class RPCConfig(TypedDict, total=False):
    """
    Type definition for full RPC configuration
    """
    ethereum: NetworkTypeConfig
    binance_smart_chain: NetworkTypeConfig
    polygon: NetworkTypeConfig

class QuickConfigLoader:
    """
    Rapid, lightweight configuration loader for immediate deployment
    """
    
    def __init__(self, config_path: str = 'configs/networks/rpc_endpoints.json'):
        """
        Initialize quick configuration loader
        
        :param config_path: Path to RPC endpoints configuration
        """
        self.config_path = config_path
        self.config: RPCConfig = self._load_config()
    
    def _load_config(self) -> RPCConfig:
        """
        Load configuration with minimal error handling
        
        :return: Loaded configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as config_file:
                config_data: RPCConfig = cast(RPCConfig, json.load(config_file))
                return config_data
        except Exception as e:
            print(f"Quick config load error: {e}")
            return {}  # type: ignore
    
    def get_endpoint(
        self, 
        network: NetworkName, 
        network_type: NetworkType = 'mainnet', 
        priority: EndpointPriority = 'primary'
    ) -> Optional[str]:
        """
        Retrieve RPC endpoint with basic substitution
        
        :param network: Blockchain network
        :param network_type: Network type
        :param priority: Endpoint priority
        :return: RPC endpoint URL
        """
        try:
            # Validate network and network type
            network_config: Dict[str, Any] = {}
            raw_network_config = safe_get(self.config, network)
            
            if isinstance(raw_network_config, dict):
                network_config = raw_network_config
            else:
                print(f"Unsupported network: {network}")
                return None
            
            network_type_config: Dict[str, Any] = {}
            raw_network_type_config = safe_get(network_config, network_type)
            
            if isinstance(raw_network_type_config, dict):
                network_type_config = raw_network_type_config
            else:
                print(f"Unsupported network type for {network}: {network_type}")
                return None
            
            # Get endpoint
            endpoint = safe_get(network_type_config, priority)
            
            if not endpoint:
                print(f"No {priority} endpoint found for {network} {network_type}")
                return None
            
            # Substitute environment variables
            return self._substitute_env_vars(str(endpoint))
        
        except Exception as e:
            print(f"Endpoint retrieval error: {e}")
            return None
    
    def _substitute_env_vars(self, endpoint: Optional[str]) -> Optional[str]:
        """
        Quickly substitute environment variables
        
        :param endpoint: Endpoint URL with potential placeholders
        :return: Endpoint with substituted variables
        """
        if not endpoint:
            return None
        
        replacements: Dict[str, str] = {
            '${INFURA_PROJECT_ID}': os.getenv('INFURA_PROJECT_ID', ''),
            '${ALCHEMY_API_KEY}': os.getenv('ALCHEMY_API_KEY', ''),
        }
        
        for placeholder, value in replacements.items():
            endpoint = endpoint.replace(placeholder, value)
        
        return endpoint

# Singleton instance for quick access
quick_config = QuickConfigLoader()

def get_rpc_endpoint(
    network: NetworkName, 
    network_type: NetworkType = 'mainnet', 
    priority: EndpointPriority = 'primary'
) -> Optional[str]:
    """
    Quick global function for endpoint retrieval
    
    :param network: Blockchain network
    :param network_type: Network type
    :param priority: Endpoint priority
    :return: RPC endpoint URL
    """
    return quick_config.get_endpoint(network, network_type, priority)

# Rapid deployment example
if __name__ == "__main__":
