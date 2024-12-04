"""Web3 utilities with retry mechanism and connection management"""

import time
import logging
from typing import Any, Optional, Callable, TypeVar, List
from functools import wraps
import os
from web3 import Web3
from web3.exceptions import BlockNotFound, ContractLogicError, TransactionNotFound
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

T = TypeVar('T')

class Web3Manager:
    """Manages Web3 connections with retry mechanism"""
    
    def __init__(
        self,
        rpc_urls: List[str],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30
    ):
        self.rpc_urls = rpc_urls
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.w3: Optional[Web3] = None
        self._initialize_web3()
    
    def _initialize_web3(self) -> None:
        """Initialize Web3 with the first working RPC endpoint"""
        for url in self.rpc_urls:
            try:
                provider = Web3.HTTPProvider(
                    url,
                    request_kwargs={'timeout': self.timeout}
                )
                w3 = Web3(provider)
                
                if w3.is_connected():
                    self.w3 = w3
                    logger.info(f"Connected to RPC: {url}")
                    return
            except Exception as e:
                logger.warning(f"Failed to connect to {url}: {e}")
                continue
        
        raise ConnectionError("Failed to connect to any RPC endpoint")
    
    def with_retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for Web3 calls with retry mechanism"""
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error = None
            
            for attempt in range(self.max_retries):
                try:
                    if not self.w3 or not self.w3.is_connected():
                        self._initialize_web3()
                    return func(*args, **kwargs)
                except (BlockNotFound, ContractLogicError, TransactionNotFound) as e:
                    # Don't retry these specific errors
                    raise e
                except (RequestException, ConnectionError) as e:
                    last_error = e
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {str(e)}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        self._initialize_web3()  # Try to reconnect
                    continue
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Unexpected error on attempt {attempt + 1}/{self.max_retries}: {str(e)}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
            
            raise last_error or Exception("All retry attempts failed")
        
        return wrapper
    
    def get_contract(self, address: str, abi: Any) -> Any:
        """Get contract instance with retry mechanism"""
        if not self.w3:
            self._initialize_web3()
        # Ensure address is checksummed
        checksummed_address = Web3.to_checksum_address(address)
        return self.w3.eth.contract(address=checksummed_address, abi=abi)
    
    @property
    def eth(self) -> Any:
        """Get eth module with automatic reconnection"""
        if not self.w3:
            self._initialize_web3()
        return self.w3.eth

def get_web3_manager() -> Web3Manager:
    """Get or create Web3Manager instance"""
    # Try to get RPC URL from environment variables
    rpc_urls = [
        os.getenv('BASE_RPC_URL', ''),
        os.getenv('BASE_BACKUP_RPC_1', ''),
        os.getenv('BASE_BACKUP_RPC_2', '')
    ]
    
    # Filter out empty URLs
    rpc_urls = [url for url in rpc_urls if url]
    
    # If no RPC URLs in env vars, use default Base mainnet RPC
    if not rpc_urls:
        rpc_urls = ['https://mainnet.base.org']
    
    return Web3Manager(rpc_urls)

# Example usage:
"""
web3_manager = get_web3_manager()

@web3_manager.with_retry
def get_latest_block():
    return web3_manager.eth.block_number

# Usage in contract calls:
@web3_manager.with_retry
def get_pool_price(pool_contract):
    return pool_contract.functions.slot0().call()
"""
