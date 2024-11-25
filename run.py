#!/usr/bin/env python3
import sys
import argparse
import logging
from typing import Optional, List, Union

# Import core components
from dashboard.monitoring import ArbitragePlatformMonitor
from configs.performance_optimized_loader import get_rpc_endpoint
from dashboard.trading_strategies import TradingStrategyManager, NetworkName

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/arbitrage_platform.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ArbitragePlatformRunner')

class ArbitragePlatform:
    """
    Comprehensive Arbitrage Trading Platform Runner
    """
    
    def __init__(
        self, 
        networks: Optional[List[NetworkName]] = None, 
        monitoring_interval: int = 60
    ):
        """
        Initialize Arbitrage Platform
        
        :param networks: Blockchain networks to monitor
        :param monitoring_interval: Monitoring interval in seconds
        """
        self.networks = networks or ['ethereum', 'binance_smart_chain']
        self.monitoring_interval = monitoring_interval
        
        # Explicitly convert NetworkName to str
        str_networks = [str(network) for network in self.networks]
        
        # Initialize core components
        self.monitor = ArbitragePlatformMonitor(
            networks=str_networks, 
            monitoring_interval=monitoring_interval
        )
        self.strategy_manager = TradingStrategyManager(self.networks)
    
    def validate_network_connectivity(self) -> bool:
        """
        Validate RPC endpoint connectivity for configured networks
        
        :return: Boolean indicating successful connectivity
        """
        logger.info("Validating network connectivity...")
        
        for network in self.networks:
            endpoint = get_rpc_endpoint(network)
            if not endpoint:
                logger.error(f"No valid RPC endpoint found for {network}")
                return False
            logger.info(f"{network.capitalize()} Endpoint: {endpoint}")
        
        return True
    
    def start(self, mode: str = 'monitoring') -> None:
        """
        Start the arbitrage platform
        
        :param mode: Operation mode (monitoring, trading, full)
        """
        # Validate network connectivity
        if not self.validate_network_connectivity():
            logger.error("Network connectivity validation failed. Exiting.")
            sys.exit(1)
        
        logger.info(f"Starting Arbitrage Platform in {mode} mode")
        
        try:
            # Start monitoring
            if mode in ['monitoring', 'full']:
                self.monitor.start_monitoring()
            
            # Start trading strategies
            if mode in ['trading', 'full']:
                self.strategy_manager.start_strategies()
            
            # Keep platform running
            while True:
                # Periodic health checks and logging
                system_metrics = self.monitor.get_system_metrics(last_n=1)
                logger.info(f"System Metrics: {system_metrics}")
                
                # Add any additional runtime management logic here
                
                # Sleep to prevent tight loop
                import time
                time.sleep(self.monitoring_interval)
        
        except KeyboardInterrupt:
            logger.info("Arbitrage Platform interrupted by user")
        except Exception as e:
            logger.error(f"Critical error in Arbitrage Platform: {e}")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """
        Gracefully stop the arbitrage platform
        """
        logger.info("Stopping Arbitrage Platform...")
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Stop trading strategies
        self.strategy_manager.stop_strategies()
        
        logger.info("Arbitrage Platform stopped successfully")

def main() -> int:
    """
    Main entry point for Arbitrage Platform
    
    :return: Exit code
    """
    parser = argparse.ArgumentParser(description='Arbitrage Trading Platform')
    parser.add_argument(
        '--mode', 
        choices=['monitoring', 'trading', 'full'], 
        default='full',
        help='Operation mode of the platform'
    )
    parser.add_argument(
        '--networks', 
        nargs='+', 
        type=str,  # Use str to allow runtime validation
        default=['ethereum', 'binance_smart_chain'],
        help='Blockchain networks to monitor'
    )
    parser.add_argument(
        '--interval', 
        type=int, 
        default=60,
        help='Monitoring interval in seconds'
    )
    
    args = parser.parse_args()
    
    # Validate network names
    valid_networks: List[NetworkName] = []
    for network in args.networks:
        if network in ['ethereum', 'binance_smart_chain', 'polygon']:
            valid_networks.append(network)  # type: ignore
        else:
            logger.warning(f"Unsupported network: {network}. Skipping.")
    
    if not valid_networks:
        logger.error("No valid networks specified. Using default.")
        valid_networks = ['ethereum', 'binance_smart_chain']
    
    platform = ArbitragePlatform(
        networks=valid_networks, 
        monitoring_interval=args.interval
    )
    
    platform.start(mode=args.mode)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
