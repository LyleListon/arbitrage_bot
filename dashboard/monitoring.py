"""
Enhanced monitoring system for arbitrage bot dashboard

@CONTEXT: System metrics collection and monitoring
@LAST_POINT: 2024-01-31 - Added trade performance tracking
@CRITICAL: Handles system resource and trade performance tracking
"""

import os
import psutil
import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, List
from threading import Lock
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class TradeMetrics:
    """Container for trade performance metrics"""
    timestamp: float
    token_pair: str
    trade_type: str  # 'buy' or 'sell'
    exchange: str
    price: float
    amount: float
    status: str  # 'success', 'failed', 'pending'
    error: Optional[str] = None
    gas_used: Optional[float] = None
    profit: Optional[float] = None


@dataclass
class SystemMetrics:
    """Container for system metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    thread_count: int
    active_connections: int
    timestamp: float
    error_rate: float = 0.0
    alert_count: int = 0


class PerformanceTracker:
    """Tracks trade performance metrics"""
    
    def __init__(self, history_size: int = 1000):
        self.trades: deque = deque(maxlen=history_size)
        self.error_window: deque = deque(maxlen=100)  # Last 100 trades for error rate
        self._lock = Lock()
        
    def add_trade(self, trade: TradeMetrics) -> None:
        """Add a trade to history"""
        with self._lock:
            self.trades.append(trade)
            self.error_window.append(1 if trade.status == 'failed' else 0)
    
    def get_error_rate(self) -> float:
        """Calculate error rate from recent trades"""
        with self._lock:
            if not self.error_window:
                return 0.0
            return (sum(self.error_window) / len(self.error_window)) * 100
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        with self._lock:
            if not self.trades:
                return {
                    'total_trades': 0,
                    'success_rate': 0,
                    'avg_profit': 0,
                    'total_profit': 0,
                    'error_rate': 0
                }
            
            successful = [t for t in self.trades if t.status == 'success']
            profits = [t.profit for t in successful if t.profit is not None]
            
            return {
                'total_trades': len(self.trades),
                'success_rate': (len(successful) / len(self.trades)) * 100,
                'avg_profit': sum(profits) / len(profits) if profits else 0,
                'total_profit': sum(profits) if profits else 0,
                'error_rate': self.get_error_rate()
            }
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent trades for display"""
        with self._lock:
            recent = list(self.trades)[-limit:]
            return [{
                'timestamp': trade.timestamp,
                'token_pair': trade.token_pair,
                'type': trade.trade_type,
                'exchange': trade.exchange,
                'price': trade.price,
                'amount': trade.amount,
                'status': trade.status,
                'profit': trade.profit
            } for trade in recent]


class AlertSystem:
    """Manages system alerts and thresholds"""
    
    def __init__(self):
        self.alerts: deque = deque(maxlen=100)
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 80,
            'error_rate': 10,
            'disk_percent': 90
        }
    
    def check_metrics(self, metrics: SystemMetrics) -> List[Dict]:
        """Check metrics against thresholds"""
        new_alerts = []
        
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            new_alerts.append({
                'type': 'warning',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'timestamp': time.time()
            })
        
        if metrics.memory_percent > self.thresholds['memory_percent']:
            new_alerts.append({
                'type': 'warning',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'timestamp': time.time()
            })
        
        if metrics.error_rate > self.thresholds['error_rate']:
            new_alerts.append({
                'type': 'error',
                'message': f'High error rate: {metrics.error_rate:.1f}%',
                'timestamp': time.time()
            })
        
        if metrics.disk_usage['percent'] > self.thresholds['disk_percent']:
            new_alerts.append({
                'type': 'warning',
                'message': f'Low disk space: {metrics.disk_usage["percent"]:.1f}%',
                'timestamp': time.time()
            })
        
        for alert in new_alerts:
            self.alerts.append(alert)
        
        return new_alerts


class MonitoringSystem:
    """Enhanced system monitoring with performance tracking"""
    
    def __init__(self):
        self._lock = Lock()
        self._last_metrics: Optional[SystemMetrics] = None
        self._last_network_io = psutil.net_io_counters()
        self._process = psutil.Process(os.getpid())
        self.performance = PerformanceTracker()
        self.alerts = AlertSystem()
        logger.info("Enhanced monitoring system initialized")

    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get current system metrics with thread safety"""
        try:
            with self._lock:
                # CPU usage (averaged over all cores)
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Disk usage for main drive
                disk = psutil.disk_usage('/')
                disk_usage = {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                }
                
                # Network I/O
                current_network = psutil.net_io_counters()
                network_io = {
                    'bytes_sent': current_network.bytes_sent - self._last_network_io.bytes_sent,
                    'bytes_recv': current_network.bytes_recv - self._last_network_io.bytes_recv,
                    'packets_sent': current_network.packets_sent - self._last_network_io.packets_sent,
                    'packets_recv': current_network.packets_recv - self._last_network_io.packets_recv
                }
                self._last_network_io = current_network
                
                # Process-specific metrics
                thread_count = self._process.num_threads()
                connections = len(self._process.connections())
                
                # Get error rate from performance tracker
                error_rate = self.performance.get_error_rate()
                
                # Create metrics object
                metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    disk_usage=disk_usage,
                    network_io=network_io,
                    thread_count=thread_count,
                    active_connections=connections,
                    timestamp=time.time(),
                    error_rate=error_rate
                )
                
                # Check for alerts
                new_alerts = self.alerts.check_metrics(metrics)
                metrics.alert_count = len(new_alerts)
                
                self._last_metrics = metrics
                return metrics
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return self._last_metrics

    def record_trade(self, trade: TradeMetrics) -> None:
        """Record a trade for performance tracking"""
        try:
            self.performance.add_trade(trade)
            logger.info(f"Recorded trade: {trade.token_pair} ({trade.status})")
        except Exception as e:
            logger.error(f"Error recording trade: {e}")

    def get_performance_data(self) -> Dict:
        """Get comprehensive performance data"""
        try:
            metrics = self.performance.get_performance_metrics()
            recent_trades = self.performance.get_recent_trades()
            current_alerts = list(self.alerts.alerts)
            
            return {
                'metrics': metrics,
                'recent_trades': recent_trades,
                'alerts': current_alerts
            }
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return {}

    def get_system_health(self) -> Dict[str, bool]:
        """Get overall system health status"""
        try:
            metrics = self.get_current_metrics()
            if not metrics:
                return {'healthy': False}
            
            # Check various health indicators
            health_checks = {
                'cpu_ok': metrics.cpu_percent < 90,
                'memory_ok': metrics.memory_percent < 90,
                'disk_ok': metrics.disk_usage['percent'] < 90,
                'error_rate_ok': metrics.error_rate < 10,
                'threads_ok': metrics.thread_count < 1000
            }
            
            return {
                'healthy': all(health_checks.values()),
                'checks': health_checks
            }
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {'healthy': False}


# Global monitor instance
monitor = MonitoringSystem()


def init_monitoring(app):
    """Initialize monitoring for Flask app"""
    try:
        @app.before_request
        def before_request():
            # Update metrics before each request
            monitor.get_current_metrics()
        
        logger.info("Enhanced monitoring initialized for Flask app")
    except Exception as e:
        logger.error(f"Error initializing monitoring: {e}")
        raise
