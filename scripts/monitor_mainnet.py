"""
Mainnet health monitoring script

@CONTEXT: Real-time monitoring of mainnet health and performance
@LAST_POINT: 2024-01-31 - Initial monitoring implementation
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from web3 import Web3
import yaml
from datetime import datetime, timedelta


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/mainnet_monitor.log')
    ]
)
logger = logging.getLogger(__name__)


class HealthCheckError(Exception):
    """Custom exception for health check failures"""
    pass


class MainnetMonitor:
    """Real-time mainnet health monitoring"""

    def __init__(self, config_path: str = 'dashboard/config/trading_config.yaml'):
        """Initialize monitor with configuration"""
        self.config = self._load_config(config_path)
        self.w3 = Web3(Web3.HTTPProvider(self.config['network']['rpc_url']))
        self.last_block = 0
        self.block_times: list = []
        self.gas_prices: list = []
        self.price_history: Dict[str, list] = {}
        self.alerts: list = []
        
        # Load contract ABIs
        self.chainlink_abi = self._load_abi('chainlink_abi.json')
        self.erc20_abi = self._load_abi('IERC20.json')
        self.router_abi = self._load_abi('IUniswapV2Router.json')
        
        # Initialize price feeds
        self.price_feeds = {}
        for pair_id, pair_config in self.config['pairs'].items():
            self.price_feeds[pair_id] = self.w3.eth.contract(
                address=pair_config['chainlink_feed'],
                abi=self.chainlink_abi
            )
            self.price_history[pair_id] = []

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration file"""
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            if config['network']['name'] != 'mainnet':
                raise HealthCheckError("Configuration not set for mainnet")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def _load_abi(self, filename: str) -> list:
        """Load contract ABI from file"""
        try:
            with open(f'dashboard/abi/{filename}', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading ABI {filename}: {e}")
            raise

    def check_network_health(self) -> bool:
        """Check overall network health"""
        try:
            # Check connection
            if not self.w3.is_connected():
                raise HealthCheckError("Lost connection to Ethereum network")
            
            # Check chain ID
            chain_id = self.w3.eth.chain_id
            if chain_id != 1:
                raise HealthCheckError(f"Wrong network: Expected mainnet (1), got {chain_id}")
            
            # Check peer count
            peer_count = self.w3.net.peer_count
            if peer_count < self.config['monitoring']['min_peer_count']:
                raise HealthCheckError(f"Low peer count: {peer_count}")
            
            # Check block progress
            current_block = self.w3.eth.block_number
            if current_block <= self.last_block:
                raise HealthCheckError("No new blocks")
            
            # Calculate block time
            if self.last_block > 0:
                last_block_time = self.w3.eth.get_block(self.last_block).timestamp
                current_block_time = self.w3.eth.get_block(current_block).timestamp
                block_time = current_block_time - last_block_time
                self.block_times.append(block_time)
                if len(self.block_times) > 100:
                    self.block_times.pop(0)
                
                # Check for slow blocks
                avg_block_time = sum(self.block_times) / len(self.block_times)
                if avg_block_time > 15:  # Ethereum target is ~12-14 seconds
                    logger.warning(f"Slow block times: {avg_block_time:.2f} seconds")
            
            self.last_block = current_block
            return True
            
        except Exception as e:
            logger.error(f"Network health check failed: {e}")
            return False

    def check_gas_prices(self) -> Optional[int]:
        """Monitor gas prices"""
        try:
            gas_price = self.w3.eth.gas_price
            self.gas_prices.append(gas_price)
            if len(self.gas_prices) > 100:
                self.gas_prices.pop(0)
            
            # Calculate average and trend
            avg_gas = sum(self.gas_prices) / len(self.gas_prices)
            if gas_price > self.config['performance']['max_gas_price'] * 10**9:
                logger.warning(f"High gas price: {gas_price / 10**9:.2f} Gwei")
            
            # Check for rapid increases
            if len(self.gas_prices) > 1:
                increase = (gas_price - self.gas_prices[-2]) / self.gas_prices[-2]
                if increase > 0.5:  # 50% increase
                    logger.warning(f"Rapid gas price increase: {increase*100:.2f}%")
            
            return gas_price
            
        except Exception as e:
            logger.error(f"Gas price check failed: {e}")
            return None

    def check_price_feeds(self) -> bool:
        """Monitor Chainlink price feeds"""
        try:
            current_time = int(time.time())
            
            for pair_id, feed in self.price_feeds.items():
                # Get latest price data
                latest = feed.functions.latestRoundData().call()
                price = latest[1]
                timestamp = latest[3]
                
                # Check price validity
                if price <= 0:
                    raise HealthCheckError(f"Invalid price from {pair_id} feed: {price}")
                
                # Check staleness
                if current_time - timestamp > 3600:
                    raise HealthCheckError(f"Stale price data for {pair_id}")
                
                # Track price history
                self.price_history[pair_id].append(price)
                if len(self.price_history[pair_id]) > 100:
                    self.price_history[pair_id].pop(0)
                
                # Check for large price movements
                if len(self.price_history[pair_id]) > 1:
                    change = (price - self.price_history[pair_id][-2]) / self.price_history[pair_id][-2]
                    if abs(change) > self.config['monitoring']['max_price_deviation']:
                        logger.warning(
                            f"Large price movement for {pair_id}: "
                            f"{change*100:.2f}%"
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"Price feed check failed: {e}")
            return False

    def check_dex_health(self) -> bool:
        """Monitor DEX health"""
        try:
            for exchange_id, exchange in self.config['exchanges'].items():
                router = self.w3.eth.contract(
                    address=exchange['router'],
                    abi=self.router_abi
                )
                
                # Check factory connection
                factory = router.functions.factory().call()
                if factory != exchange['factory']:
                    raise HealthCheckError(
                        f"Factory mismatch for {exchange_id}: "
                        f"Expected {exchange['factory']}, got {factory}"
                    )
                
                # Check liquidity for each pair
                for pair_id, pair_config in self.config['pairs'].items():
                    try:
                        # Get amounts out for a test amount
                        test_amount = 10 ** pair_config['decimals']  # 1 token
                        amounts = router.functions.getAmountsOut(
                            test_amount,
                            [
                                pair_config['base_token'],
                                pair_config['quote_token']
                            ]
                        ).call()
                        
                        if amounts[1] <= 0:
                            logger.warning(f"No liquidity for {pair_id} on {exchange_id}")
                            
                    except Exception as e:
                        logger.warning(
                            f"Error checking liquidity for {pair_id} "
                            f"on {exchange_id}: {e}"
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"DEX health check failed: {e}")
            return False

    def run_health_check(self) -> None:
        """Run comprehensive health check"""
        try:
            # Network health
            network_healthy = self.check_network_health()
            if not network_healthy:
                self.alerts.append("Network health check failed")
            
            # Gas prices
            gas_price = self.check_gas_prices()
            if gas_price is None:
                self.alerts.append("Gas price check failed")
            
            # Price feeds
            feeds_healthy = self.check_price_feeds()
            if not feeds_healthy:
                self.alerts.append("Price feed check failed")
            
            # DEX health
            dex_healthy = self.check_dex_health()
            if not dex_healthy:
                self.alerts.append("DEX health check failed")
            
            # Log status
            status = "✅" if not self.alerts else "❌"
            logger.info(
                f"Health check {status} - "
                f"Block: {self.last_block}, "
                f"Gas: {gas_price/10**9:.2f} Gwei"
            )
            
            # Clear alerts after logging
            self.alerts = []
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def monitor(self, interval: int = 15) -> None:
        """Run continuous monitoring"""
        logger.info(
            f"Starting mainnet monitoring\n"
            f"Network: {self.config['network']['name']}\n"
            f"Interval: {interval} seconds"
        )
        
        while True:
            try:
                self.run_health_check()
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(interval)


def main() -> int:
    """Main entry point"""
    try:
        monitor = MainnetMonitor()
        monitor.monitor()
        return 0
    except Exception as e:
        logger.error(f"Monitor initialization failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
