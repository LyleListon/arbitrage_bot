# mypy: disable-error-code="import,misc"
"""
Flask application for the arbitrage bot dashboard.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal
import json

from flask import Flask, render_template
from flask_socketio import SocketIO
try:
    from flask_cors import CORS
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("flask-cors not installed. Please install with: pip install flask-cors")
    raise
from dotenv import load_dotenv
import yaml
from web3 import Web3

from dashboard.blockchain_monitor import BlockchainMonitor
from dashboard.advanced_arbitrage_detector import AdvancedArbitrageDetector


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reduce websocket logger verbosity
logging.getLogger('engineio.server').setLevel(logging.WARNING)
logging.getLogger('socketio.server').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)


# Custom JSON encoder to handle Decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


# Load environment variables and config
load_dotenv()
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Debug: Print loaded config
logger.info("Loaded config:")
logger.info(f"Supported tokens from config: {config.get('supported_tokens', [])}")

# Initialize Flask app
app = Flask(__name__)
CORS(app)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    json=json,
    json_encoder=DecimalEncoder,
    ping_timeout=60,  # Increase ping timeout
    ping_interval=25,  # Increase ping interval
    max_http_buffer_size=1000000  # Increase buffer size
)

# Initialize Sepolia connection
SEPOLIA_RPC = config['networks']['ethereum_sepolia']['rpc_url']
FACTORY_ADDRESS = config['factory_address']
PATHFINDER_ADDRESS = config['pathfinder_address']
ARBITRAGE_BOT_ADDRESS = config['arbitrage_bot_address']
CHECK_INTERVAL = config.get('check_interval', 30)  # Get check_interval from config, default to 30 seconds

w3_sepolia = Web3(Web3.HTTPProvider(SEPOLIA_RPC))
blockchain_monitor: Optional[BlockchainMonitor] = None
arbitrage_detector: Optional[AdvancedArbitrageDetector] = None

if w3_sepolia.is_connected():
    logger.info(f"Connected to Sepolia network at {SEPOLIA_RPC}")

    # Initialize blockchain monitor with ArbitrageBot address
    blockchain_monitor = BlockchainMonitor(w3_sepolia, ARBITRAGE_BOT_ADDRESS)
    logger.info(f"Blockchain monitor initialized for ArbitrageBot at {ARBITRAGE_BOT_ADDRESS}")

    # Get supported tokens
    supported_tokens = config.get('supported_tokens', [])
    logger.info(f"Raw supported tokens from config: {supported_tokens}")

    # Convert to list of addresses, ensuring proper string format
    token_addresses: List[str] = []
    for token in supported_tokens:
        if isinstance(token, dict) and 'address' in token:
            token_addresses.append(token['address'])
    logger.info(f"Extracted token addresses: {token_addresses}")

    # Initialize arbitrage detector with PathFinder
    detector_config = {
        'PATHFINDER_ADDRESS': PATHFINDER_ADDRESS,
        'MIN_PROFIT_THRESHOLD': float(config.get('min_profit_percentage', 0.005)),
        'MAX_SLIPPAGE': float(config.get('slippage_tolerance', 0.01)),
        'SUPPORTED_TOKENS': token_addresses,
        'WALLET_ADDRESS': ARBITRAGE_BOT_ADDRESS  # Use bot address as wallet
    }
    logger.info(f"Detector config: {detector_config}")

    arbitrage_detector = AdvancedArbitrageDetector(
        networks=['Ethereum Sepolia'],
        w3_connections={'Ethereum Sepolia': w3_sepolia},
        config=detector_config
    )
    logger.info(f"Arbitrage detector initialized with PathFinder at {PATHFINDER_ADDRESS}")
else:
    logger.error("Failed to connect to Sepolia network")


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics"""
    try:
        return {
            'cpu_percent': 0,
            'memory_percent': 0
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {}


@app.route('/')
def index() -> str:
    """Render dashboard index page"""
    return render_template('index.html')


def emit_stats() -> None:
    """Emit stats to connected clients"""
    try:
        # Get basic metrics
        system_metrics = get_system_metrics()

        # Get real blockchain data
        if blockchain_monitor:
            transactions = blockchain_monitor.get_transactions()
            stats = blockchain_monitor.get_profit_stats()
            balance = blockchain_monitor.get_contract_balance()
            tx_count = blockchain_monitor.get_transaction_count()
        else:
            transactions = []
            stats = {'total_profit': 0.0, 'total_cost': 0.0, 'net_profit': 0.0, 'avg_gas_price': 0.0}
            balance = 0.0
            tx_count = 0

        # Get real arbitrage opportunities
        if arbitrage_detector and w3_sepolia:
            try:
                gas_prices = {'Ethereum Sepolia': float(w3_sepolia.eth.gas_price) / 1e9}  # Convert to Gwei
                token_prices: Dict[str, Dict[str, float]] = {}  # Get from price feeds if needed
                opportunities = arbitrage_detector.detect_arbitrage(token_prices, gas_prices)
                if opportunities:  # Only log when opportunities are found
                    logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            except Exception as e:
                logger.error(f"Error detecting arbitrage: {e}")
                opportunities = []
        else:
            opportunities = []

        data = {
            'timestamp': int(datetime.now().timestamp()),
            'system_metrics': system_metrics,
            'transactions': transactions,
            'stats': stats,
            'balance': float(balance),
            'transaction_count': tx_count,
            'network': 'Ethereum Sepolia',
            'contract_address': ARBITRAGE_BOT_ADDRESS,
            'opportunities': opportunities
        }

        # Only log data if there are opportunities or other significant changes
        if opportunities or tx_count > 0:
            logger.debug(f"Emitting stats: {data}")
        socketio.emit('stats_update', data)

    except Exception as e:
        logger.error(f"Error in emit_stats: {e}")


def background_stats() -> None:
    """Background task to emit stats periodically"""
    while True:
        emit_stats()
        socketio.sleep(CHECK_INTERVAL)  # Use configured check interval


@socketio.on('connect')
def handle_connect() -> None:
    """Handle client connection"""
    logger.info("Client connected")
    emit_stats()


@socketio.on('disconnect')
def handle_disconnect() -> None:
    """Handle client disconnection"""
    logger.info("Client disconnected")


@socketio.on('request_update')
def handle_request_update() -> None:
    """Handle request for immediate update"""
    logger.info("Received request for immediate update")
    emit_stats()


def start_app() -> Flask:
    """Initialize and start the application"""
    logger.info("Starting dashboard application")
    socketio.start_background_task(background_stats)
    return app


if __name__ == '__main__':
    app = start_app()
    socketio.run(
        app,
        debug=True,
        use_reloader=False,
        ping_timeout=60,  # Increase ping timeout
        ping_interval=25  # Increase ping interval
    )
