"""Enhanced arbitrage bot dashboard"""

import os
import logging
from flask import Flask, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from dashboard.monitoring import init_monitoring, monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardApp:
    """Dashboard application with enhanced monitoring and alerts"""
    
    def __init__(self, network: str = "base"):
        """Initialize dashboard application"""
        self.network = network
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.config['SECRET_KEY'] = os.urandom(24)
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        
        # Initialize monitoring
        self.monitor = init_monitoring(self.app)
        
        # Initialize SocketIO
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='gevent',
            logger=True,
            engineio_logger=True,
            ping_timeout=5,
            ping_interval=2
        )
        
        # Set up routes
        self._setup_routes()
        
        # Set up WebSocket handlers
        self._setup_websocket_handlers()
        
        logger.info(f"Enhanced dashboard app initialized for network: {network}")
    
    def _setup_routes(self):
        """Set up Flask routes"""
        
        @self.app.route('/')
        def index():
            """Render main dashboard page"""
            try:
                return render_template('index.html', network=self.network)
            except Exception as e:
                logger.error(f"Error rendering index: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get current statistics with enhanced metrics"""
            try:
                # Get system metrics
                metrics = self.monitor.get_current_metrics()
                
                # Get performance data
                performance_data = self.monitor.get_performance_data()
                
                # Get system health
                health = self.monitor.get_system_health()
                
                stats = {
                    'status': 'success',
                    'data': {
                        'network': self.network,
                        'system_metrics': {
                            'cpu_percent': metrics.cpu_percent if metrics else None,
                            'memory_percent': metrics.memory_percent if metrics else None,
                            'network_io': metrics.network_io if metrics else None,
                            'active_connections': metrics.active_connections if metrics else None,
                            'error_rate': metrics.error_rate if metrics else None
                        },
                        'performance': {
                            'total_opportunities': performance_data.get('total_opportunities', 0),
                            'average_spread': performance_data.get('average_spread', 0.0),
                            'average_profit': performance_data.get('average_profit', 0.0),
                            'total_profit': performance_data.get('total_profit', 0.0),
                            'executed_trades': performance_data.get('executed_trades', 0)
                        },
                        'price_data': performance_data.get('price_data', []),
                        'health': health
                    }
                }
                
                # Emit stats via WebSocket
                self.socketio.emit('stats_update', stats['data'], namespace='/dashboard')
                
                return jsonify(stats)
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                }), 500
    
    def _setup_websocket_handlers(self):
        """Set up WebSocket event handlers"""
        
        @self.socketio.on('connect', namespace='/dashboard')
        def handle_connect():
            """Handle client connection"""
            try:
                # Get current stats
                stats = self.app.view_functions['get_stats']()
                data = stats.get_json() if hasattr(stats, 'get_json') else stats
                
                # Send initial update
                emit('stats_update', data.get('data', {}))
                logger.info("Client connected and received initial update")
                
                # Set up periodic updates
                @self.socketio.on('request_update', namespace='/dashboard')
                def handle_update_request():
                    try:
                        stats = self.app.view_functions['get_stats']()
                        data = stats.get_json() if hasattr(stats, 'get_json') else stats
                        emit('stats_update', data.get('data', {}))
                    except Exception as e:
                        logger.error(f"Error sending update: {e}")
                        emit('error', {'message': str(e)})
                
            except Exception as e:
                logger.error(f"Error sending initial update: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('disconnect', namespace='/dashboard')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info("Client disconnected")
        
        @self.socketio.on_error(namespace='/dashboard')
        def handle_error(e):
            """Handle WebSocket errors"""
            logger.error(f"WebSocket error: {e}")
            emit('error', {'message': str(e)})
    
    def run(self, host: str = '127.0.0.1', port: int = 5002):
        """Run the enhanced dashboard application"""
        try:
            logger.info(f"Starting enhanced dashboard on {self.network}")
            self.socketio.run(
                self.app,
                host=host,
                port=port,
                debug=True,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
            raise

def main():
    """Main entry point for the dashboard application"""
    try:
        app = DashboardApp(network='base')
        app.run(port=5002)
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        raise

if __name__ == '__main__':
    main()
