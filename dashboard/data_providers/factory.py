"""
Factory for creating data providers
"""
import os
from typing import Dict
from .base_provider import BaseDataProvider
from .simulated_provider import SimulatedDataProvider
from .live_provider import LiveDataProvider


class DataProviderFactory:
    """Factory for creating data providers"""
    
    @staticmethod
    def create_provider(provider_type: str = None, **kwargs) -> BaseDataProvider:
        """
        Create a data provider instance
        
        Args:
            provider_type: Type of provider ('simulated' or 'live')
            **kwargs: Additional arguments for the provider
        
        Returns:
            Instance of BaseDataProvider
        """
        # If no type specified, check environment variable
        if not provider_type:
            provider_type = os.getenv('DATA_PROVIDER_TYPE', 'simulated').lower()
        
        if provider_type == 'live':
            required_args = ['rpc_url', 'price_feeds']
            missing_args = [arg for arg in required_args if arg not in kwargs]
            if missing_args:
                raise ValueError(f"Missing required arguments for live provider: {missing_args}")
            return LiveDataProvider(**kwargs)
        
        # Default to simulated provider
        return SimulatedDataProvider()


# Default Chainlink price feed addresses for Sepolia
SEPOLIA_PRICE_FEEDS: Dict[str, str] = {
    'ETH': '0x694AA1769357215DE4FAC081bf1f309aDC325306',
    'BTC': '0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43',
    'USDC': '0xA2F78ab2355fe2f984D808B5CeE7FD0A93D5270E',
    'DAI': '0x14866185B1962B63C3Ea9E03Bc1da838bab34C19',
    'LINK': '0xc59E3633BAAC79493d908e63626716e204A45EdF'
}


def get_provider(force_type: str = None) -> BaseDataProvider:
    """
    Get a data provider instance using environment configuration
    
    Args:
        force_type: Override the environment configuration with this provider type
        
    Returns:
        Instance of BaseDataProvider
    """
    provider_type = force_type or os.getenv('DATA_PROVIDER_TYPE', 'simulated').lower()
    
    if provider_type == 'live':
        # Get configuration from environment
        rpc_url = os.getenv('SEPOLIA_RPC_URL')
        if not rpc_url:
            raise ValueError("SEPOLIA_RPC_URL environment variable not set")
        
        return DataProviderFactory.create_provider(
            provider_type='live',
            rpc_url=rpc_url,
            price_feeds=SEPOLIA_PRICE_FEEDS
        )
    
    return DataProviderFactory.create_provider('simulated')
