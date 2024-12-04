"""Enhanced monitoring system with price and opportunity tracking"""
import os
import sys
import time
import logging
import threading
from collections import deque
import psutil
from typing import List, Optional, Dict, Any, Union, Type, NamedTuple
from datetime import datetime, timedelta
from .trading_strategies import NetworkName
from .price_analysis import PriceAnalyzer
from .data_cleanup import DatabaseCleaner

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
        db_path: str = 'arbitrage_bot.db',
        metrics_retention: int = 3600  # Keep 1 hour of metrics in memory
    ):
        self.networks = networks
        self.monitoring_interval = monitoring_interval
        self.metrics_retention = metrics_retention
        self.logger = logging.getLogger('ArbitragePlatformMonitor')
        self.monitor_thread = None
        self.cleanup_thread = None
        self.is_monitoring = False
        
        # Initialize components
        self.db_path = os.path.join(os.path.dirname(__file__), '..', db_path)
        self.price_analyzer = PriceAnalyzer(self.db_path)
        self.db_cleaner = DatabaseCleaner(self.db_path)
        
        # Use deque with maxlen for automatic size management
        self.blockchain_metrics = {
            network: deque(maxlen=self.metrics_retention) 
            for network in networks
        }
        
        # Price monitoring with size limits
        self.price_metrics = {}
        
        # Performance tracking with recent data only
        self.performance_data = {
            'metrics': {},
            'recent_trades': deque(maxlen=100),
            'alerts': deque(maxlen=50),
            'opportunities': deque(maxlen=100),
            'price_data': deque(maxlen=100)
        }
        
        # Error tracking
        self.error_counts = {}
        self.last_error_cleanup = time.time()

    def start_monitoring(self) -> None:
        """Start monitoring blockchain networks"""
        if self.is_monitoring:
            self.logger.warning("Monitoring is already running")
            return
        
        self.is_monitoring = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop, 
            daemon=True
        )
        self.monitor_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
        
        self.logger.info("Monitoring and cleanup threads started")

    def _monitoring_loop(self) -> None:
        """Continuous monitoring loop"""
        while self.is_monitoring:
            try:
                self._collect_system_metrics()
                self._collect_price_metrics()
                self._update_performance_data()
                self._cleanup_error_counts()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                self._track_error('monitoring_loop')
                time.sleep(self.monitoring_interval)

    def _cleanup_loop(self) -> None:
        """Database cleanup loop"""
        while self.is_monitoring:
            try:
                self.db_cleaner.cleanup_old_data()
                self.db_cleaner.optimize_database()
                time.sleep(86400)  # Daily cleanup
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                time.sleep(3600)  # Retry in 1 hour

    def _track_error(self, error_source: str) -> None:
        """Track error occurrences"""
        self.error_counts[error_source] = self.error_counts.get(error_source, 0) + 1

    def _cleanup_error_counts(self) -> None:
        """Clean up error counts hourly"""
        current_time = time.time()
        if current_time - self.last_error_cleanup > 3600:
            self.error_counts.clear()
            self.last_error_cleanup = current_time

    def _collect_system_metrics(self) -> None:
        """Collect system metrics"""
        try:
            metrics = SystemMetrics(
                cpu_percent=psutil.cpu_percent(),
                memory_percent=psutil.virtual_memory().percent,
                network_io={
                    'bytes_sent': psutil.net_io_counters().bytes_sent,
                    'bytes_recv': psutil.net_io_counters().bytes_recv
                },
                active_connections=len(psutil.net_connections()),
                error_rate=sum(self.error_counts.values()) / 3600
            )
            self.performance_data['metrics'] = metrics
        except Exception as e:
            self.logger.error(f"System metrics error: {e}")
            self._track_error('system_metrics')

    def _collect_price_metrics(self) -> None:
        """Collect price metrics"""
        try:
            token_pairs = ['WETH/USDC', 'WETH/USDbC', 'USDC/USDbC']
            exchanges = ['uniswap_v3']
            
            for pair in token_pairs:
                for exchange in exchanges:
                    stats = self.price_analyzer.get_price_statistics(pair, exchange)
                    if stats:
                        key = f"{pair}_{exchange}"
                        if key not in self.price_metrics:
                            self.price_metrics[key] = deque(maxlen=self.metrics_retention)
                        
                        self.price_metrics[key].append(PriceMetrics(
                            token_pair=pair,
                            exchange=exchange,
                            current_price=stats['current_price'],
                            volatility=stats['volatility'],
                            volume=None,
                            timestamp=time.time()
                        ))
        except Exception as e:
            self.logger.error(f"Price metrics error: {e}")
            self._track_error('price_metrics')

    def _update_performance_data(self) -> None:
        """Update performance data"""
        try:
            perf = self.price_analyzer.get_historical_performance(1440)
            self.performance_data.update({
                'total_opportunities': perf['total_opportunities'],
                'average_spread': perf['average_spread'],
                'average_profit': perf['average_profit'],
                'total_profit': perf['total_profit'],
                'executed_trades': perf['executed_trades']
            })
        except Exception as e:
            self.logger.error(f"Performance update error: {e}")
            self._track_error('performance_data')

    def stop_monitoring(self) -> None:
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        self.logger.info("Monitoring stopped")

    def get_system_metrics(self, last_n: Optional[int] = None) -> Dict[str, Any]:
        """Get system metrics"""
        metrics = {
            'timestamp': time.time(),
            'networks': self.networks,
            'blockchain_metrics': {}
        }
        
        for network in self.networks:
            network_metrics = list(self.blockchain_metrics[network])
            if last_n is not None:
                network_metrics = network_metrics[-last_n:]
            metrics['blockchain_metrics'][network] = network_metrics
        
        return metrics

    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get current metrics"""
        return self.performance_data.get('metrics')

    def get_performance_data(self) -> Dict[str, Any]:
        """Get performance data"""
        return {
            'metrics': self.performance_data.get('metrics', {}),
            'recent_trades': list(self.performance_data['recent_trades']),
            'alerts': list(self.performance_data['alerts']),
            'price_data': list(self.performance_data['price_data']),
            'total_opportunities': self.performance_data.get('total_opportunities', 0),
            'average_spread': self.performance_data.get('average_spread', 0.0),
            'average_profit': self.performance_data.get('average_profit', 0.0),
            'total_profit': self.performance_data.get('total_profit', 0.0),
            'executed_trades': self.performance_data.get('executed_trades', 0)
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
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
        
        if metrics.error_rate > 10:  # More than 10 errors per hour
            health_status = 'warning'
            warnings.append('High error rate')
        
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
            'error_rate': metrics.error_rate,
            'warnings': warnings,
            'trading_metrics': {
                'opportunities': perf_data['total_opportunities'],
                'executed_trades': perf_data['executed_trades'],
                'total_profit': perf_data['total_profit']
            }
        }

def init_monitoring(app: Optional[Any] = None) -> ArbitragePlatformMonitor:
    """Initialize monitoring"""
    monitor = ArbitragePlatformMonitor()
    monitor.start_monitoring()
    return monitor

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        monitor = init_monitoring()
        time.sleep(300)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
