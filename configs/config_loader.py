import os
import json
from typing import Dict, Any, Optional, Union, TypedDict, cast, Literal, Type, TypeVar

def load_env_file(env_path: str = '.env') -> Dict[str, str]:
    """
    Manually load environment variables from a .env file
    
    :param env_path: Path to the .env file
    :return: Dictionary of environment variables
    """
    env_vars: Dict[str, str] = {}
    
    try:
        with open(env_path, 'r') as env_file:
            for line in env_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('\'"')
                        env_vars[key] = value
                    except ValueError:
                        print(f"Skipping invalid line in .env file: {line}")
    except FileNotFoundError:
        print(f"No .env file found at {env_path}")
    except Exception as e:
        print(f"Error reading .env file: {e}")
    
    return env_vars

def set_env_vars(env_vars: Dict[str, str]) -> bool:
    """
    Set environment variables from a dictionary
    
    :param env_vars: Dictionary of environment variables
    :return: Boolean indicating successful environment variable setting
    """
    try:
        for key, value in env_vars.items():
            if key not in os.environ:
                os.environ[key] = value
        return True
    except Exception as e:
        print(f"Error setting environment variables: {e}")
        return False

# Literal types for network and endpoint configurations
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

class RPCConfigLoader:
    """
    Secure RPC endpoint configuration loader
    Handles multi-network, multi-environment RPC endpoint management
    """
    
    def __init__(
        self, 
        config_path: str = 'configs/networks/rpc_endpoints.json', 
        env_path: str = '.env'
    ):
        """
        Initialize RPC configuration loader
        
        :param config_path: Path to RPC endpoints configuration
        :param env_path: Path to .env file
        """
        # Load environment variables
        env_vars = load_env_file(env_path)
        set_env_vars(env_vars)
        
        # Load RPC configuration
        self.config_path = config_path
        self.rpc_config: RPCConfig = self._load_rpc_config()
    
    def _load_rpc_config(self) -> RPCConfig:
        """
        Load RPC configuration from JSON file
        
        :return: Dictionary of RPC endpoint configurations
        """
        try:
            with open(self.config_path, 'r') as config_file:
                config_data: RPCConfig = cast(RPCConfig, json.load(config_file))
                return config_data
        except FileNotFoundError:
            print(f"RPC configuration file not found: {self.config_path}")
            return {}  # type: ignore
        except json.JSONDecodeError:
            print(f"Invalid JSON in RPC configuration: {self.config_path}")
            return {}  # type: ignore
    
    def get_rpc_endpoint(
        self, 
        network: NetworkName, 
        network_type: NetworkType = 'mainnet', 
        priority: EndpointPriority = 'primary'
    ) -> Optional[str]:
        """
        Retrieve a specific RPC endpoint with environment variable substitution
        
        :param network: Blockchain network
        :param network_type: Network type
        :param priority: Endpoint priority
        :return: Configured RPC endpoint with substituted credentials
        """
        try:
            # Validate network and network type
            network_config = safe_get(self.rpc_config, network)
            if not network_config:
                print(f"Unsupported network: {network}")
                return None
            
            network_type_config = safe_get(network_config, network_type)
            if not network_type_config:
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
            print(f"Error retrieving RPC endpoint: {e}")
            return None
    
    def _substitute_env_vars(self, endpoint: str) -> str:
        """
        Substitute environment variables in endpoint URL
        
        :param endpoint: Endpoint URL with potential env var placeholders
        :return: Endpoint with environment variables replaced
        """
        # Common API key environment variables
        env_vars: Dict[str, str] = {
            'INFURA_PROJECT_ID': os.getenv('INFURA_PROJECT_ID', ''),
            'ALCHEMY_API_KEY': os.getenv('ALCHEMY_API_KEY', ''),
            'QUICKNODE_API_KEY': os.getenv('QUICKNODE_API_KEY', '')
        }
        
        # Substitute environment variables
        for var, value in env_vars.items():
            endpoint = endpoint.replace(f'${{{var}}}', value)
        
        return endpoint
    
    def get_all_network_endpoints(self) -> Dict[NetworkName, Dict[NetworkType, Dict[EndpointPriority, str]]]:
        """
        Retrieve all configured network endpoints
        
        :return: Dictionary of network endpoints
        """
        network_endpoints: Dict[NetworkName, Dict[NetworkType, Dict[EndpointPriority, str]]] = {}
        
        for network, network_types in self.rpc_config.items():
            if not isinstance(network_types, dict):
                continue
            
            network_endpoints[cast(NetworkName, network)] = {}
            
            for network_type, endpoints in network_types.items():
                if not isinstance(endpoints, dict):
                    continue
                
                network_endpoints[cast(NetworkName, network)][cast(NetworkType, network_type)] = {
                    cast(EndpointPriority, priority): self._substitute_env_vars(str(endpoint))
                    for priority, endpoint in endpoints.items()
                }
        
        return network_endpoints

def load_rpc_config() -> RPCConfigLoader:
    """
    Convenience function to load RPC configuration
    
    :return: Configured RPCConfigLoader instance
    """
    return RPCConfigLoader()

# Example usage
if __name__ == "__main__":
    config_loader = load_rpc_config()
    
    # Get Ethereum mainnet primary endpoint
    eth_endpoint = config_loader.get_rpc_endpoint('ethereum', 'mainnet')
    print(f"Ethereum Mainnet Endpoint: {eth_endpoint}")
    
    # Get all configured network endpoints
    all_endpoints = config_loader.get_all_network_endpoints()
    print("All Network Endpoints:")
    print(json.dumps(all_endpoints, indent=2))
