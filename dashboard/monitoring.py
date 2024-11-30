"""Enhanced monitoring system with price and opportunity tracking"""

import os
import sys
import time
import logging
import threading
import psutil
from typing import List, Optional, Dict, Any, Union, Type, NamedTuple
from .trading_strategies import NetworkName
from .price_analysis import PriceAnalyzer

class SystemMetrics(NamedTuple):
    """Structured system metrics"""
    cpu_percent: float
    memory_percent: float
    network_io: Dict[str, float]
    active_connections: int
    error_rate: float

class PriceMetrics(NamedTuple):
    """Price monitoring metrics"""
    token_pair: str
    exchange: str
    current_price: float
    volatility: float
    volume: Optional[float]
    timestamp: float

class ArbitragePlatformMonitor:
    """Comprehensive monitoring system for arbitrage trading platform"""
    
    def __init__(
        self, 
        networks: List[str] = ['base'],
        monitoring_interval: int = 60,
        db_path: str = 'arbitrage_bot.db'
    ):
        self.networks: List[str] = networks
        self.monitoring_interval: int = monitoring_interval
        self.logger: logging.Logger = logging.getLogger('ArbitragePlatformMonitor')
        self.monitor_thread: Optional[threading.Thread] = None
        self.is_monitoring: bool = False
        
        # Initialize price analyzer with database path
        self.db_path = os.path.join(os.path.dirname(__file__), '..', db_path)
        self.price_analyzer = PriceAnalyzer(self.db_path)
        
        # Metrics storage
        self.blockchain_metrics: Dict[str, List[Dict[str, Any]]] = {
            network: [] for network in networks
        }
        
        # Price monitoring
        self.price_metrics: Dict[str, List[PriceMetrics]] = {}
        
        # Performance tracking
        self.performance_data: Dict[str, Any] = {
            'metrics': {},
            'recent_trades': [],
            'alerts': [],
            'opportunities': []
        }
    
    def start_monitoring(self) -> None:
        """Start monitoring blockchain networks"""
        if self.is_monitoring:
            self.logger.warning("Monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, 
            daemon=True
        )
        self.monitor_thread.start()
        self.logger.info("Monitoring started")
    
    def _monitoring_loop(self) -> None:
        """Continuous monitoring loop for blockchain networks"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Collect price metrics
                self._collect_price_metrics()
                
                # Collect network metrics
                current_metrics = {
                    network: {
                        'timestamp': time.time(),
                        'network': network
                    } for network in self.networks
                }
                
                # Store metrics
                for network, metrics in current_metrics.items():
                    self.blockchain_metrics[network].append(metrics)
                
                # Get historical performance
                self._update_performance_data()
                
                self.logger.info("Monitoring system active")
                time.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_system_metrics(self) -> None:
        """Collect and store system-level metrics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()
            network_io = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            }
            active_connections = len(psutil.net_connections())
            error_rate = 0.0
            
            self.performance_data['metrics'] = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                network_io=network_io,
                active_connections=active_connections,
                error_rate=error_rate
            )
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_price_metrics(self) -> None:
        """Collect and store price-related metrics"""
        try:
            token_pairs = [
                'WETH/USDC',
                'WETH/DAI',
                'USDC/DAI'
            ]
            exchanges = ['baseswap', 'aerodrome']
            
            current_time = int(time.time())
            for token_pair in token_pairs:
                for exchange in exchanges:
                    stats = self.price_analyzer.get_price_statistics(token_pair, exchange)
                    if stats:
                        metrics = PriceMetrics(
                            token_pair=token_pair,
                            exchange=exchange,
                            current_price=stats['current_price'],
                            volatility=stats['volatility'],
                            volume=None,  # Could be added if available
                            timestamp=current_time
                        )
                        
                        key = f"{token_pair}_{exchange}"
                        if key not in self.price_metrics:
                            self.price_metrics[key] = []
                        self.price_metrics[key].append(metrics)
                        
                        # Keep only last hour of metrics
                        cutoff = current_time - 3600
                        self.price_metrics[key] = [
                            m for m in self.price_metrics[key]
                            if m.timestamp > cutoff
                        ]
                        
                        # Add to performance data for immediate display
                        if 'price_data' not in self.performance_data:
                            self.performance_data['price_data'] = []
                            
                        # Update or add price data
                        price_entry = {
                            'pair': token_pair,
                            'baseswap_price': None,
                            'aerodrome_price': None,
                            'spread': None,
                            'timestamp': current_time
                        }
                        
                        # Find existing entry or use new one
                        existing_entry = next(
                            (item for item in self.performance_data['price_data'] 
                             if item['pair'] == token_pair),
                            None
                        )
                        
                        if existing_entry:
                            price_entry = existing_entry
                        else:
                            self.performance_data['price_data'].append(price_entry)
                        
                        # Update price for specific exchange
                        if exchange == 'baseswap':
                            price_entry['baseswap_price'] = stats['current_price']
                        elif exchange == 'aerodrome':
                            price_entry['aerodrome_price'] = stats['current_price']
                        
                        # Calculate spread if both prices are available
                        if (price_entry['baseswap_price'] is not None and 
                            price_entry['aerodrome_price'] is not None):
                            base_price = price_entry['baseswap_price']
                            spread = abs(price_entry['aerodrome_price'] - base_price) / base_price * 100
                            price_entry['spread'] = round(spread, 2)
                        
        except Exception as e:
            self.logger.error(f"Error collecting price metrics: {e}")
    
    def _update_performance_data(self) -> None:
        """Update performance tracking data"""
        try:
            # Get historical performance for last 24 hours
            performance = self.price_analyzer.get_historical_performance(1440)
            
            self.performance_data.update({
                'total_opportunities': performance['total_opportunities'],
                'average_spread': performance['average_spread'],
                'average_profit': performance['average_profit'],
                'total_profit': performance['total_profit'],
                'executed_trades': performance['executed_trades']
            })
        except Exception as e:
            self.logger.error(f"Error updating performance data: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring blockchain networks"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("Monitoring stopped")
    
    def get_system_metrics(self, last_n: Optional[int] = None) -> Dict[str, Any]:
        """Retrieve current system metrics"""
        metrics: Dict[str, Any] = {
            'timestamp': time.time(),
            'networks': self.networks,
            'blockchain_metrics': {}
        }
        
        for network in self.networks:
            network_metrics = self.blockchain_metrics.get(network, [])
            if last_n is not None:
                network_metrics = network_metrics[-last_n:]
            metrics['blockchain_metrics'][network] = network_metrics
        
        return metrics
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent system metrics"""
        return self.performance_data.get('metrics')
    
    def get_performance_data(self) -> Dict[str, Any]:
        """Retrieve performance-related data"""
        return {
            'metrics': self.performance_data.get('metrics', {}),
            'recent_trades': self.performance_data.get('recent_trades', []),
            'alerts': self.performance_data.get('alerts', []),
            'price_data': self.performance_data.get('price_data', []),
            'total_opportunities': self.performance_data.get('total_opportunities', 0),
            'average_spread': self.performance_data.get('average_spread', 0.0),
            'average_profit': self.performance_data.get('average_profit', 0.0),
            'total_profit': self.performance_data.get('total_profit', 0.0),
            'executed_trades': self.performance_data.get('executed_trades', 0)
        }
    
    def get_price_metrics(self, token_pair: str, exchange: str, 
                         last_n: Optional[int] = None) -> List[PriceMetrics]:
        """Get price metrics for a specific token pair and exchange"""
        key = f"{token_pair}_{exchange}"
        metrics = self.price_metrics.get(key, [])
        if last_n is not None:
            metrics = metrics[-last_n:]
        return metrics
    
    def get_system_health(self) -> Dict[str, Any]:
        """Assess overall system health"""
        metrics = self.get_current_metrics()
        
        if not metrics:
            return {
                'status': 'unknown',
                'message': 'Unable to retrieve system metrics'
            }
        
        health_status = 'healthy'
        warnings = []
        
        if metrics.cpu_percent > 80:
            health_status = 'warning'
            warnings.append('High CPU usage')
        
        if metrics.memory_percent > 90:
            health_status = 'critical'
            warnings.append('High memory usage')
        
        # Check trading performance
        perf_data = self.get_performance_data()
        if perf_data['total_opportunities'] > 0:
            success_rate = perf_data['executed_trades'] / perf_data['total_opportunities']
            if success_rate < 0.1:
                health_status = 'warning'
                warnings.append('Low opportunity execution rate')
        
        return {
            'status': health_status,
            'cpu_usage': metrics.cpu_percent,
            'memory_usage': metrics.memory_percent,
            'warnings': warnings,
            'trading_metrics': {
                'opportunities': perf_data['total_opportunities'],
                'executed_trades': perf_data['executed_trades'],
                'total_profit': perf_data['total_profit']
            }
        }

# Global monitor instance
monitor = ArbitragePlatformMonitor()

def init_monitoring(app: Optional[Any] = None) -> ArbitragePlatformMonitor:
    """Initialize monitoring for the application"""
    global monitor
    monitor = ArbitragePlatformMonitor()
    monitor.start_monitoring()
    return monitor

def main() -> None:
    """Example usage of monitoring system"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        monitor = init_monitoring()
        time.sleep(300)
    except Exception as e:
        logging.error(f"Monitoring initialization error: {e}")
    except KeyboardInterrupt:
        print("\nMonitoring interrupted")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()
