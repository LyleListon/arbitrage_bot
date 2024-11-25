# mypy: disable-error-code="import,misc"
"""
Flask application for the arbitrage bot dashboard.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal
import json

# Robust YAML import with fallback
try:
    import yaml
except ImportError:
    try:
        import ruamel.yaml as yaml
    except ImportError:
        yaml = None
        logging.error("No YAML library available. Please install PyYAML or ruamel.yaml")

from flask import Flask, render_template
from flask_socketio import SocketIO
try:
    from flask_cors import CORS
except ImportError:
    logger = logging.getLogger(__name__)
    logger.error("flask-cors not installed. Please install with: pip install flask-cors")
    raise
from dotenv import load_dotenv
from web3 import Web3

from dashboard.blockchain_monitor import BlockchainMonitor
from dashboard.advanced_arbitrage_detector import AdvancedArbitrageDetector
from dashboard.monitoring import ArbitragePlatformMonitor, init_monitoring

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

# Robust config loading
if yaml is None:
    logger.error("Cannot load configuration: No YAML library available")
    config: Dict[str, Any] = {}
else:
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        config = {}

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

# Rest of the file remains the same as in the previous version
