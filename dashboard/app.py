import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from decimal import Decimal
import json
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from web3 import Web3
import threading
import time

from dashboard.monitoring import ArbitragePlatformMonitor, init_monitoring
from dashboard.price_analysis import PriceAnalyzer
from dashboard.trading_strategies import ArbitrageStrategy, NetworkName

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DecimalJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal objects"""
    def default(self, obj: Any) -> Union[float, str, Any]:
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure SocketIO with the custom JSON encoder
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    json=json,
    json_encoder=DecimalJSONEncoder
)

# Initialize monitoring and price analysis
monitor = init_monitoring()
price_analyzer = PriceAnalyzer()

# Initialize arbitrage strategy for Base network
strategy = ArbitrageStrategy(
    network=NetworkName.BASE,
    exchanges=['baseswap', 'aerodrome']
)

# Initialize Web3 connection
if strategy.web3_client and hasattr(strategy.web3_client.provider, 'endpoint_uri'):
    provider_uri = str(strategy.web3_client.provider.endpoint_uri)
else:
    provider_uri = "https://base-mainnet.infura.io/v3/863c326dab1a444dba3f41ae7a07ccce"
w3 = Web3(Web3.HTTPProvider(provider_uri))

def background_task() -> None:
    """Background task to emit updates periodically"""
    while True:
        try:
            # Get system metrics
            metrics = monitor.get_current_metrics()
            
            # Convert Decimal values to float
            system_metrics = {
                'cpu_percent': float(metrics.cpu_percent) if metrics else 0,
                'memory_percent': float(metrics.memory_percent) if metrics else 0
            }
            
            # Get network stats
            network_stats = get_network_stats()
            logger.info(f"Network stats: {network_stats}")
            
            # Get price data
            price_data = get_price_data()
            logger.info(f"Price data: {price_data}")
            
            # Get opportunities
            opportunities = get_arbitrage_opportunities()
            logger.info(f"Opportunities: {opportunities}")
            
            # Prepare update data
            update_data = {
                'system_metrics': system_metrics,
                'network_stats': network_stats,
                'price_data': price_data,
                'opportunities': opportunities
            }
            
            logger.info(f"Emitting update data: {json.dumps(update_data, cls=DecimalJSONEncoder)}")
            socketio.emit('stats_update', update_data)
            
        except Exception as e:
            logger.error(f"Error in background task: {e}")
        
        # Sleep for 5 seconds before next update
        time.sleep(5)

@app.route('/')
def index() -> str:
    """Render the dashboard interface"""
    return render_template('index.html')

def get_network_stats() -> Dict[str, Any]:
    """Get current network statistics"""
    try:
        gas_price = w3.eth.gas_price
        stats = {
            'block_number': w3.eth.block_number,
            'gas_price': float(w3.from_wei(gas_price, 'gwei')),
            'timestamp': datetime.now().timestamp()
        }
        logger.info(f"Network stats: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error getting network stats: {e}")
        return {}

def get_price_data() -> List[Dict[str, Any]]:
    """Get real price data from DEXes"""
    try:
        price_data = []
        token_pairs = [('WETH', 'USDC'), ('WETH', 'DAI'), ('USDC', 'DAI')]
        
        for token_in, token_out in token_pairs:
            logger.info(f"Getting prices for {token_in}/{token_out}")
            baseswap_price = strategy.get_token_price('baseswap', token_in, token_out)
            aerodrome_price = strategy.get_token_price('aerodrome', token_in, token_out)
            
            if baseswap_price and aerodrome_price:
                spread = abs(baseswap_price - aerodrome_price)
                avg_price = (baseswap_price + aerodrome_price) / 2
                spread_percent = (spread / avg_price) * 100
                
                pair_data = {
                    'pair': f'{token_in}/{token_out}',
                    'baseswap_price': float(baseswap_price),
                    'aerodrome_price': float(aerodrome_price),
                    'spread': float(spread_percent),
                    'timestamp': datetime.now().timestamp()
                }
                logger.info(f"Price data for {token_in}/{token_out}: {pair_data}")
                price_data.append(pair_data)
                
                # Store price data for analysis
                price_analyzer.add_price_record(
                    token_pair=f'{token_in}/{token_out}',
                    exchange='baseswap',
                    price=float(baseswap_price)
                )
                price_analyzer.add_price_record(
                    token_pair=f'{token_in}/{token_out}',
                    exchange='aerodrome',
                    price=float(aerodrome_price)
                )
        
        return price_data
    except Exception as e:
        logger.error(f"Error getting price data: {e}")
        return []

def get_arbitrage_opportunities() -> List[Dict[str, Any]]:
    """Get real arbitrage opportunities"""
    try:
        opportunities = strategy.find_arbitrage_opportunities()
        logger.info(f"Raw opportunities: {opportunities}")
        
        # Enhance opportunities with gas costs and net profit calculations
        enhanced_opportunities = []
        for opp in opportunities:
            try:
                gas_price = w3.eth.gas_price
                estimated_gas = 200000  # Estimated gas for a swap
                gas_cost_eth = w3.from_wei(gas_price * estimated_gas, 'ether')
                gas_cost_usd = float(gas_cost_eth * Decimal(str(opp['baseswap_price'])))
                
                # Calculate potential profit
                amount_in = Decimal('1')  # 1 token
                price_diff = abs(Decimal(str(opp['aerodrome_price'])) - Decimal(str(opp['baseswap_price'])))
                potential_profit = float(amount_in * price_diff)
                
                enhanced_opp = {
                    'timestamp': datetime.now().timestamp(),
                    'token_in': opp['token_in'],
                    'token_out': opp['token_out'],
                    'direction': opp['direction'],
                    'spread_percent': float(opp['spread_percent']),
                    'gas_cost_usd': gas_cost_usd,
                    'potential_profit_usd': potential_profit,
                    'net_profit_usd': potential_profit - gas_cost_usd
                }
                logger.info(f"Enhanced opportunity: {enhanced_opp}")
                
                if enhanced_opp['net_profit_usd'] > 0:
                    enhanced_opportunities.append(enhanced_opp)
                    
            except Exception as e:
                logger.error(f"Error enhancing opportunity: {e}")
                
        return enhanced_opportunities
    except Exception as e:
        logger.error(f"Error getting arbitrage opportunities: {e}")
        return []

@socketio.on('request_update')
def handle_update_request() -> None:
    """Handle client requests for data updates"""
    try:
        # Get system metrics
        metrics = monitor.get_current_metrics()
        
        # Convert Decimal values to float
        system_metrics = {
            'cpu_percent': float(metrics.cpu_percent) if metrics else 0,
            'memory_percent': float(metrics.memory_percent) if metrics else 0
        }
        
        # Prepare update data
        update_data = {
            'system_metrics': system_metrics,
            'network_stats': get_network_stats(),
            'price_data': get_price_data(),
            'opportunities': get_arbitrage_opportunities()
        }
        
        logger.info(f"Emitting update data from request: {json.dumps(update_data, cls=DecimalJSONEncoder)}")
        socketio.emit('stats_update', update_data)
        
    except Exception as e:
        logger.error(f"Error handling update request: {e}")

def main() -> None:
    """Main entry point"""
    try:
        # Validate network connection
        if not strategy.validate_network():
            raise Exception("Failed to connect to Base network")
            
        logger.info("Starting arbitrage dashboard...")
        
        # Start background task
        thread = threading.Thread(target=background_task)
        thread.daemon = True
        thread.start()
        
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        raise

if __name__ == '__main__':
    main()
