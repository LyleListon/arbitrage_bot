import logging
from typing import Dict, Optional
from web3 import Web3

logger = logging.getLogger(__name__)


class GasPriceFetcher:
    def __init__(self, w3_connections: Dict[str, Web3], config: Dict) -> None:
        self.w3_connections = w3_connections
        self.config = config

    def fetch_gas_prices(self) -> Dict[str, Optional[float]]:
        """Fetch current gas prices for each network"""
        gas_prices: Dict[str, Optional[float]] = {}

        for network, w3 in self.w3_connections.items():
            try:
                if w3.is_connected():
                    gas_price = w3.eth.gas_price
                    gas_price_gwei = w3.from_wei(gas_price, 'gwei')
                    gas_prices[network] = float(gas_price_gwei)
                else:
                    gas_prices[network] = None
            except Exception as e:
                logger.error(f"Error fetching gas price for {network}: {e}")
                gas_prices[network] = None

        return gas_prices
