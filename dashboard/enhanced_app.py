"""
Enhanced arbitrage bot dashboard

@CONTEXT: Flask-based web dashboard with improved reliability and monitoring
@LAST_POINT: 2024-01-31 - Added performance tracking and alerts
"""

import os
import logging
import argparse
from flask import Flask, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
try:
    from flask_cors import CORS
except ImportError:
    print("Error: flask-cors package is required. Install with: pip install flask-cors")
    raise
from web3 import Web3
from dotenv import load_dotenv

from dashboard.data_providers.live_provider import LiveDataProvider
from dashboard.monitoring import init_monitoring, monitor
from dashboard.config.config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the enhanced arbitrage dashboard')
    parser.add_argument(
        '--network',
        type=str,
        default='development',
        help='Network to run on (development/sepolia/mainnet)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5002,
        help='Port to run the dashboard on'
    )
    return parser.parse_args()


class DashboardApp:
    """Dashboard application with enhanced monitoring and alerts"""
    
    def __init__(self, network: str = "development"):
        """Initialize dashboard application"""
        self.network = network
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.config['SECRET_KEY'] = os.urandom(24)
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        
        # Initialize monitoring
        init_monitoring(self.app)
        
        # Initialize SocketIO with improved reliability
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='gevent',
            logger=True,
            engineio_logger=True,
            ping_timeout=5,
            ping_interval=2,
            max_http_buffer_size=1e8
        )
        
        # Load network configuration
        self._load_network_config()
        
        # Set up routes
        self._setup_routes()
        
        # Set up WebSocket handlers
        self._setup_websocket_handlers()
        
        logger.info(f"Enhanced dashboard app initialized for network: {network}")
    
    def _load_network_config(self):
        """Load network-specific configuration"""
        try:
            # Load environment variables
            env_path = os.path.join(os.path.dirname(__file__), f'.env.{self.network}')
            load_dotenv(env_path)
            
            # Load configuration
            config_loader = ConfigLoader(network=self.network)
            self.config = config_loader.load_config()
            
            # Initialize Web3
            network_config = config_loader.get_network_config()
            self.w3 = Web3(Web3.HTTPProvider(network_config.rpc_url))
            
            if not self.w3.is_connected():
                raise Exception(f"Failed to connect to {self.network} network")
            
            # Set up account if private key available
            private_key = os.getenv('PRIVATE_KEY')
            if private_key:
                self.account = self.w3.eth.account.from_key(private_key)
            else:
                logger.warning("No private key found")
                self.account = None
            
            # Initialize data provider
            self.data_provider = LiveDataProvider(network=self.network)
            logger.info(f"Data provider initialized: {self.data_provider.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Error loading network configuration: {e}")
            raise
    
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
        
        @self.app.route('/favicon.ico')
        def favicon():
            """Serve favicon"""
            return send_from_directory(
                os.path.join(self.app.root_path, 'static'),
                'favicon.ico',
                mimetype='image/vnd.microsoft.icon'
            )
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get current statistics with enhanced metrics"""
            try:
                # Get market data
                market_data = self.data_provider.get_market_data()
                
                # Get system metrics
                metrics = monitor.get_current_metrics()
                
                # Get performance data
                performance_data = monitor.get_performance_data()
                
                # Get system health
                health = monitor.get_system_health()
                
                stats = {
                    'status': 'success',
                    'data': {
                        'network': self.network,
                        'market_data': market_data,
                        'system_metrics': {
                            'cpu_percent': metrics.cpu_percent if metrics else None,
                            'memory_percent': metrics.memory_percent if metrics else None,
                            'network_io': metrics.network_io if metrics else None,
                            'active_connections': metrics.active_connections if metrics else None,
                            'error_rate': metrics.error_rate if metrics else None
                        },
                        'performance': performance_data.get('metrics', {}),
                        'trade_history': performance_data.get('recent_trades', []),
                        'alerts': performance_data.get('alerts', []),
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
        """Set up WebSocket event handlers with improved reliability"""
        
        @self.socketio.on('connect', namespace='/dashboard')
        def handle_connect():
            """Handle client connection"""
            try:
                # Send immediate update
                stats = self.app.view_functions['get_stats']()
                emit('stats_update', stats.json['data'])
                logger.info("Client connected and received initial update")
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
        args = parse_args()
        app = DashboardApp(network=args.network)
        app.run(port=args.port)
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")
        raise


if __name__ == '__main__':
    main()
