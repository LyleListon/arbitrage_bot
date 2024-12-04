import os
import json
import time
from typing import Dict, Any, Optional, Union, TypedDict, cast, Literal, Type, TypeVar, Tuple
from functools import lru_cache
import threading
import timeit

# Literal types for network configurations
NetworkName = Literal['ethereum', 'binance_smart_chain', 'polygon', 'base']
NetworkType = Literal['mainnet', 'testnet']
EndpointPriority = Literal['primary', 'secondary', 'fallback']

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
    base: NetworkTypeConfig

class PerformanceOptimizedConfigLoader:
    """
    High-performance configuration loader with advanced caching and optimization techniques
    """
    
    _instance: Optional['PerformanceOptimizedConfigLoader'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'PerformanceOptimizedConfigLoader':
        """
        Singleton implementation with thread-safe instantiation
        
        :return: Singleton instance of the configuration loader
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cast('PerformanceOptimizedConfigLoader', cls._instance)
    
    def __init__(
        self, 
        config_path: str = 'configs/networks/rpc_endpoints.json',
        cache_size: int = 128,
        cache_ttl: int = 3600  # 1 hour cache timeout
    ) -> None:
        """
        Initialize performance-optimized configuration loader
        
        :param config_path: Path to configuration file
        :param cache_size: LRU cache size for endpoint lookups
        :param cache_ttl: Cache time-to-live in seconds
        """
        # Prevent re-initialization
        if hasattr(self, '_initialized'):
            return
        
        self._config_path: str = config_path
        self._cache_ttl: int = cache_ttl
        
        # Thread-safe configuration loading
        with self._lock:
            self._config: RPCConfig = self._load_config()
            self._last_load_time: float = time.time()
        
        # Performance-optimized caching
        self._endpoint_cache: Dict[str, str] = {}
        self._cached_get_endpoint = lru_cache(maxsize=cache_size)(self._get_endpoint_uncached)
        
        # Mark as initialized
        self._initialized = True
    
    def _load_config(self) -> RPCConfig:
        """
        Load configuration with error handling and performance tracking
        
        :return: Loaded configuration dictionary
        """
        start_time = time.time()
        try:
            with open(self._config_path, 'r') as config_file:
                config: RPCConfig = cast(RPCConfig, json.load(config_file))
            
            load_time = time.time() - start_time
            print(f"Configuration loaded in {load_time:.4f} seconds")
            return config
        except Exception as e:
            print(f"Configuration loading error: {e}")
            return {}  # type: ignore
    
    def _should_reload_config(self) -> bool:
        """
        Determine if configuration should be reloaded based on TTL
        
        :return: Boolean indicating whether to reload configuration
        """
        current_time = time.time()
        return current_time - self._last_load_time > self._cache_ttl
    
    def _get_endpoint_uncached(
        self, 
        network: NetworkName, 
        network_type: NetworkType = 'mainnet', 
        priority: EndpointPriority = 'primary'
    ) -> Optional[str]:
        """
        Retrieve RPC endpoint with minimal overhead
        
        :param network: Blockchain network
        :param network_type: Network type
        :param priority: Endpoint priority
        :return: RPC endpoint URL
        """
        try:
            # Reload configuration if needed
            if self._should_reload_config():
                with self._lock:
                    self._config = self._load_config()
                    self._last_load_time = time.time()
            
            network_config: Dict[str, Any] = self._config.get(network, {})
            network_type_config: Dict[str, Any] = network_config.get(network_type, {})
            endpoint: Optional[str] = network_type_config.get(priority)
            
            return self._substitute_env_vars(endpoint) if endpoint else None
            
        except Exception as e:
            print(f"Endpoint retrieval error: {e}")
            return None
    
    def get_endpoint(
        self, 
        network: NetworkName, 
        network_type: NetworkType = 'mainnet', 
        priority: EndpointPriority = 'primary'
    ) -> Optional[str]:
        """
        Cached endpoint retrieval with performance optimization
        
        :param network: Blockchain network
        :param network_type: Network type
        :param priority: Endpoint priority
        :return: RPC endpoint URL
        """
        cache_key = f"{network}:{network_type}:{priority}"
        
        # Check cache first
        if cache_key in self._endpoint_cache:
            return self._endpoint_cache[cache_key]
        
        # Retrieve and cache endpoint
        endpoint = self._cached_get_endpoint(network, network_type, priority)
        if endpoint:
            self._endpoint_cache[cache_key] = endpoint
        
        return endpoint
    
    def _substitute_env_vars(self, endpoint: Optional[str]) -> Optional[str]:
        """
        Efficiently substitute environment variables
        
        :param endpoint: Endpoint URL with potential placeholders
        :return: Endpoint with substituted variables
        """
        if not endpoint:
            return None
        
        # Predefined environment variable mapping
        env_vars: Dict[str, str] = {
            '${INFURA_PROJECT_ID}': os.getenv('INFURA_PROJECT_ID', ''),
            '${ALCHEMY_API_KEY}': os.getenv('ALCHEMY_API_KEY', ''),
            '${QUICKNODE_API_KEY}': os.getenv('QUICKNODE_API_KEY', '')
        }
        
        # Efficient string replacement
        for placeholder, value in env_vars.items():
            endpoint = endpoint.replace(placeholder, value)
        
        return endpoint
    
    def get_all_endpoints(self) -> Dict[NetworkName, Dict[NetworkType, Dict[EndpointPriority, str]]]:
        """
        Retrieve all network endpoints with caching
        
        :return: Dictionary of all network endpoints
        """
        # Use cached configuration
        all_endpoints: Dict[NetworkName, Dict[NetworkType, Dict[EndpointPriority, str]]] = {}
        
        for network, network_types in self._config.items():
            if not isinstance(network_types, dict):
                continue
            
            all_endpoints[cast(NetworkName, network)] = {}
            for network_type, endpoints in network_types.items():
                if not isinstance(endpoints, dict):
                    continue
                
                all_endpoints[cast(NetworkName, network)][cast(NetworkType, network_type)] = {
                    cast(EndpointPriority, priority): self._substitute_env_vars(endpoint) or ''
                    for priority, endpoint in endpoints.items()
                }
        
        return all_endpoints

# Performance-optimized singleton instance
performance_config_loader = PerformanceOptimizedConfigLoader()

def get_rpc_endpoint(
    network: NetworkName, 
    network_type: NetworkType = 'mainnet', 
    priority: EndpointPriority = 'primary'
) -> Optional[str]:
    """
    Convenience function for endpoint retrieval
    
    :param network: Blockchain network
    :param network_type: Network type
    :param priority: Endpoint priority
    :return: RPC endpoint URL
    """
    return performance_config_loader.get_endpoint(network, network_type, priority)

# Performance benchmarking
def benchmark_endpoint_retrieval() -> Tuple[float, Optional[str]]:
    """
    Benchmark endpoint retrieval performance
    
    :return: Tuple of average retrieval time and retrieved endpoint
    """
    def retrieve_endpoint() -> Optional[str]:
        return get_rpc_endpoint('base')  # Changed to benchmark Base endpoint
    
    # Measure retrieval time
    retrieval_time = timeit.timeit(retrieve_endpoint, number=1000)
    avg_time = retrieval_time / 1000
    
    print(f"Average endpoint retrieval time: {avg_time:.6f} seconds")
    
    return avg_time, retrieve_endpoint()

if __name__ == "__main__":
    benchmark_endpoint_retrieval()
