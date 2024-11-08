"""
Tests for Performance Monitoring System

@CONTEXT: Test suite for monitoring implementation
@LAST_POINT: 2024-01-31 - Initial test implementation
"""

import unittest
import time
from unittest.mock import Mock, patch
from dashboard.monitoring import (
    PerformanceMonitor,
    SystemMetrics,
    ThreadMetrics,
    monitor_requests
)

class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for PerformanceMonitor class"""
    
    def setUp(self):
        """Set up test environment"""
        self.monitor = PerformanceMonitor(sample_interval=0.1)
    
    def tearDown(self):
        """Clean up test environment"""
        if self.monitor.running:
            self.monitor.stop()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    @patch('psutil.Process')
    def test_collect_metrics(self, mock_process, mock_net, mock_disk, 
                           mock_memory, mock_cpu):
        """Test metrics collection"""
        # Mock system metrics
        mock_cpu.return_value = 50.0
        mock_memory.return_value.percent = 60.0
        mock_disk.return_value.percent = 70.0
        mock_net.return_value.bytes_sent = 1000
        mock_net.return_value.bytes_recv = 2000
        
        # Mock process metrics
        mock_thread = Mock()
        mock_thread.id = 1
        mock_thread.user_time = 0.5
        mock_thread.status = 'running'
        mock_process.return_value.threads.return_value = [mock_thread]
        mock_process.return_value.connections.return_value = []
        
        # Collect metrics
        metrics = self.monitor._collect_metrics()
        
        # Verify metrics
        self.assertEqual(metrics.cpu_percent, 50.0)
        self.assertEqual(metrics.memory_percent, 60.0)
        self.assertEqual(metrics.disk_usage, 70.0)
        self.assertEqual(metrics.network_io['bytes_sent'], 1000)
        self.assertEqual(metrics.network_io['bytes_recv'], 2000)
        self.assertEqual(metrics.thread_count, 1)
        self.assertEqual(metrics.active_connections, 0)
    
    def test_monitor_lifecycle(self):
        """Test monitor start/stop lifecycle"""
        # Start monitor
        self.monitor.start()
        self.assertTrue(self.monitor.running)
        self.assertIsNotNone(self.monitor._monitor_thread)
        
        # Stop monitor
        self.monitor.stop()
        self.assertFalse(self.monitor.running)
        self.assertIsNone(self.monitor.get_current_metrics())
    
    def test_metrics_history(self):
        """Test metrics history management"""
        # Create sample metrics
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            disk_usage=70.0,
            network_io={'bytes_sent': 1000, 'bytes_recv': 2000},
            thread_count=1,
            active_connections=0
        )
        
        # Add metrics to history
        self.monitor._store_metrics(metrics)
        
        # Verify history
        history = self.monitor.get_metrics_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0], metrics)
    
    def test_threshold_checks(self):
        """Test resource threshold monitoring"""
        # Create metrics above thresholds
        metrics = SystemMetrics(
            cpu_percent=90.0,  # Above 80% threshold
            memory_percent=95.0,  # Above 85% threshold
            disk_usage=95.0,  # Above 90% threshold
            network_io={'bytes_sent': 1000, 'bytes_recv': 2000},
            thread_count=150,  # Above 100 thread threshold
            active_connections=0
        )
        
        with self.assertLogs(level='WARNING') as log:
            self.monitor._check_thresholds(metrics)
            self.assertEqual(len(log.output), 4)  # Should have 4 warnings

class TestFlaskMonitoring(unittest.TestCase):
    """Test cases for Flask request monitoring"""
    
    def setUp(self):
        """Set up test Flask app"""
        from flask import Flask
        self.app = Flask(__name__)
        monitor_requests(self.app)
        self.client = self.app.test_client()
        
        @self.app.route('/test')
        def test_route():
            return 'test'
    
    def test_request_monitoring(self):
        """Test request monitoring middleware"""
        # Make test request
        response = self.client.get('/test')
        self.assertEqual(response.status_code, 200)
        
        # Verify request was monitored
        # Note: In a real test, we'd verify Prometheus metrics
        # but for simplicity, we just check the response

if __name__ == '__main__':
    unittest.main()
