<<<<<<< HEAD
"""Enhanced Price Analysis Module with Real-time Integration and Price Impact Calculation"""
=======
"nk ""Real-time Price Analysis Module with DEX Integration"""
>>>>>>> 245fdac14b0b9bc65ffd42e3056011a2ab2b4d30

from web3 import Web3
import logging
<<<<<<< HEAD
from typing import Dict, Deque, Optional, Tuple
from decimal import Decimal
from collections import deque
from dataclasses import dataclass
from datetime import datetime
=======
import time
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, Any, Optional, List, TypedDict, cast, Union
from decimal import Decimal
import statistics
import os
from .web3_utils import get_web3_manager
from .dex_interface import get_dex_interface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
>>>>>>> 245fdac14b0b9bc65ffd42e3056011a2ab2b4d30

@dataclass
class PricePoint:
    price: Decimal
    timestamp: datetime

@dataclass
class VolumeData:
    volume: Decimal
    timestamp: datetime

class PriceAnalyzer:
<<<<<<< HEAD
    def __init__(self, db_path: str = 'arbitrage_bot.db', history_window: int = 3600) -> None:
        self.db_path = db_path
        # Use Infura endpoint for Base network
        infura_url = "https://base-mainnet.infura.io/v3/863c326dab1a444dba3f41ae7a07ccce"
        self.w3 = Web3(Web3.HTTPProvider(infura_url, request_kwargs={'timeout': 60}))
        self.last_prices: Dict[str, Decimal] = {}
        self.price_history: Dict[str, Deque[PricePoint]] = {}
        self.volume_history: Dict[str, Deque[VolumeData]] = {}
        self.history_window = history_window  # Keep 1 hour of history
        self.last_block_number = None
        self.min_confidence_threshold = Decimal('0.7')  # Minimum confidence score to report opportunity
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Verified working pool addresses on Base
        self.POOL_ADDRESSES = {
            'ETH/USDC/0.05%': '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18',
            'WETH/USDC/0.05%': '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18',
            'UNI/USDC/0.3%': '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18'
        }

        # UniswapV3 pool ABI (minimal for price and liquidity calculation)
        self.POOL_ABI = [
            {
                "constant": True,
                "inputs": [],
                "name": "slot0",
                "outputs": [
                    {"name": "sqrtPriceX96", "type": "uint160"},
                    {"name": "tick", "type": "int24"},
                    {"name": "observationIndex", "type": "uint16"},
                    {"name": "observationCardinality", "type": "uint16"},
                    {"name": "observationCardinalityNext", "type": "uint16"},
                    {"name": "feeProtocol", "type": "uint8"},
                    {"name": "unlocked", "type": "bool"}
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "liquidity",
                "outputs": [{"name": "", "type": "uint128"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }
        ]

    def get_token_price(self, token_in: str, token_out: str, fee_tier: str) -> Optional[Tuple[Decimal, Decimal, Dict[Decimal, Decimal]]]:
        """Get current token price and calculate price impact"""
        try:
            pair_name = f"{token_in}/{token_out}/{fee_tier}"
            pool_address = self.POOL_ADDRESSES.get(pair_name)
            
            if not pool_address:
                return None
            
            pool_contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(pool_address),
                abi=self.POOL_ABI
            )
            
            # Get current price
            slot0 = pool_contract.functions.slot0().call()
            sqrtPriceX96 = Decimal(str(slot0[0]))
            price = (sqrtPriceX96 / Decimal(str(2**96))) ** Decimal('2')
            
            # Convert price to USD terms
            if token_in == 'ETH' or token_in == 'WETH':
                price = Decimal('1') / price
            
            # Get pool liquidity
            liquidity = Decimal(str(pool_contract.functions.liquidity().call()))
            
            # Calculate price change
            price_change = Decimal('0')
            if pair_name in self.last_prices:
                price_change = ((price - self.last_prices[pair_name]) / self.last_prices[pair_name]) * Decimal('100')
            self.last_prices[pair_name] = price
            
            # Calculate price impact for different sizes
            price_impacts = {
                Decimal('1'): self._calculate_price_impact(Decimal('1'), liquidity),
                Decimal('5'): self._calculate_price_impact(Decimal('5'), liquidity),
                Decimal('10'): self._calculate_price_impact(Decimal('10'), liquidity)
            }
            
            # Update history
            self._update_price_history(pair_name, price)
            
            return price, price_change, price_impacts
            
        except Exception as e:
            self.logger.error(f"Error getting price for {token_in}/{token_out}: {str(e)}")
=======
    """Price analysis with multi-DEX support"""
    
    def __init__(self, db_path: str = 'arbitrage_bot.db'):
        self.db_path = db_path
        self.logger = logging.getLogger('PriceAnalyzer')
        
        # Initialize components
        self.web3_manager = get_web3_manager()
        self.dex_interface = get_dex_interface()
        
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables"""
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create indices for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_dex_prices_token_pair 
                ON dex_prices(token_pair)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_dex_prices_dex 
                ON dex_prices(dex)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trades_token_pair 
                ON trades(token_pair)
            ''')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_price_statistics(self, token_pair: str, exchange: str, 
                           timeframe_minutes: int = 60) -> Optional[Dict[str, float]]:
        """Get price statistics for a token pair on a specific exchange"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Calculate time window
            cutoff_time = datetime.now() - timedelta(minutes=timeframe_minutes)
            
            # Query price data
            cursor.execute('''
                SELECT price
                FROM dex_prices
                WHERE token_pair = ? 
                AND dex = ?
                AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (token_pair, exchange, int(cutoff_time.timestamp())))
            
            prices = [row['price'] for row in cursor.fetchall()]
            
            if not prices:
                # Get current price from DEX
                current_price = self.dex_interface.get_price(exchange, token_pair)
                if current_price is None:
                    return None
                
                return {
                    'current_price': float(current_price),
                    'mean_price': float(current_price),
                    'min_price': float(current_price),
                    'max_price': float(current_price),
                    'volatility': 0.0,
                    'std_dev': 0.0,
                    'samples': 1
                }
            
            # Calculate statistics
            current_price = prices[0]
            mean_price = statistics.mean(prices)
            min_price = min(prices)
            max_price = max(prices)
            std_dev = statistics.stdev(prices) if len(prices) > 1 else 0
            
            # Calculate volatility (standard deviation / mean * 100)
            volatility = (std_dev / mean_price * 100) if mean_price > 0 else 0
            
            return {
                'current_price': current_price,
                'mean_price': mean_price,
                'min_price': min_price,
                'max_price': max_price,
                'volatility': volatility,
                'std_dev': std_dev,
                'samples': len(prices)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting price statistics: {e}")
>>>>>>> 245fdac14b0b9bc65ffd42e3056011a2ab2b4d30
            return None

<<<<<<< HEAD
    def get_volatility(self, pair_name: str) -> Decimal:
        """Calculate volatility as average absolute percentage change"""
        try:
            if pair_name not in self.price_history:
                return Decimal('0')
            
            history = list(self.price_history[pair_name])
            if len(history) < 2:
                return Decimal('0')
            
            # Calculate percentage changes
            changes = []
            for i in range(1, len(history)):
                prev_price = history[i-1].price
                curr_price = history[i].price
                
                if prev_price != 0:
                    pct_change = abs((curr_price - prev_price) / prev_price * Decimal('100'))
                    changes.append(pct_change)
            
            if not changes:
                return Decimal('0')
            
            # Calculate average of changes
            total = sum(changes)
            count = Decimal(str(len(changes)))
            
            return total / count
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {str(e)}")
            return Decimal('0')

    def get_volume(self, pair_name: str) -> Decimal:
        """Get trading volume over the last 5 minutes"""
        try:
            if pair_name not in self.volume_history:
                return Decimal('0')
            
            recent_volume = sum(v.volume for v in self.volume_history[pair_name])
            return recent_volume
            
        except Exception as e:
            self.logger.error(f"Error getting volume: {str(e)}")
            return Decimal('0')

    def _calculate_price_impact(self, amount: Decimal, liquidity: Decimal) -> Decimal:
        """Calculate price impact percentage for a given trade size"""
        if liquidity == 0:
            return Decimal('100')
        
        # Base impact
        base_impact = Decimal('0.001')  # 0.1%
        
        # Scale impact based on size
        size_multiplier = amount / Decimal('1')
        if amount > Decimal('10'):
            size_multiplier = size_multiplier * Decimal('1.5')  # Extra scaling for large trades
        
        # Calculate final impact
        impact = (base_impact + (amount / liquidity)) * size_multiplier * Decimal('100')
        
        return min(impact, Decimal('100'))

    def _update_price_history(self, pair_name: str, price: Decimal) -> None:
        """Update price history for a token pair"""
        if pair_name not in self.price_history:
            self.price_history[pair_name] = deque(maxlen=self.history_window)
        
        self.price_history[pair_name].append(
            PricePoint(price=price, timestamp=datetime.now())
        )

    def check_arbitrage_opportunity(self, prices: Dict[str, Decimal], min_spread_percent: float = 0.1) -> Optional[dict]:
        """Check for arbitrage opportunities between pairs"""
=======
    def get_historical_performance(self, timeframe_minutes: int = 1440) -> HistoricalPerformance:
        """Get historical performance metrics"""
        conn = None
>>>>>>> 245fdac14b0b9bc65ffd42e3056011a2ab2b4d30
        try:
            opportunities = []
            min_spread = Decimal(str(min_spread_percent))
            
<<<<<<< HEAD
            for pair1, price1 in prices.items():
                for pair2, price2 in prices.items():
                    if pair1 != pair2:
                        spread = abs(price1 - price2) / price1 * Decimal('100')
                        if spread > min_spread:
                            opportunities.append({
                                'pair1': pair1,
                                'pair2': pair2,
                                'spread_percent': float(spread),
                                'estimated_profit': float(abs(price1 - price2)),
                                'confidence_score': float(self._calculate_arb_confidence(spread))
                            })
            
            return max(opportunities, key=lambda x: x['spread_percent']) if opportunities else None
            
        except Exception as e:
            self.logger.error(f"Error checking arbitrage: {str(e)}")
            return None

    def _calculate_arb_confidence(self, spread: Decimal) -> Decimal:
        """Calculate confidence score for arbitrage opportunity"""
        base_score = Decimal('0.7')
        
        # Adjust based on spread size
        if spread > Decimal('1.0'):  # 1%
            base_score += Decimal('0.2')
        elif spread < Decimal('0.2'):  # 0.2%
            base_score -= Decimal('0.1')
        
        return min(base_score, Decimal('1.0'))
=======
            # Calculate time window
            cutoff_time = int((datetime.now() - timedelta(minutes=timeframe_minutes)).timestamp())
            
            # Get trade statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    AVG(profit) as avg_profit,
                    SUM(profit) as total_profit
                FROM trades
                WHERE timestamp > ?
            ''', (cutoff_time,))
            
            trade_stats = cursor.fetchone()
            
            # Get opportunity statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_opportunities,
                    AVG(confidence) as avg_confidence
                FROM opportunity_scores
                WHERE timestamp > ?
            ''', (cutoff_time,))
            
            opp_stats = cursor.fetchone()
            
            # Get average spread
            cursor.execute('''
                SELECT AVG(spread_percent) as avg_spread
                FROM opportunity_history
                WHERE timestamp > ?
            ''', (cutoff_time,))
            
            spread_stats = cursor.fetchone()
            
            return {
                'total_opportunities': opp_stats['total_opportunities'],
                'average_spread': spread_stats['avg_spread'] or 0.0,
                'average_profit': trade_stats['avg_profit'] or 0.0,
                'total_profit': trade_stats['total_profit'] or 0.0,
                'executed_trades': trade_stats['total_trades'],
                'timeframe_minutes': timeframe_minutes
            }
            
        except Exception as e:
            self.logger.error(f"Error getting historical performance: {e}")
            return {
                'total_opportunities': 0,
                'average_spread': 0.0,
                'average_profit': 0.0,
                'total_profit': 0.0,
                'executed_trades': 0,
                'timeframe_minutes': timeframe_minutes
            }
        finally:
            if conn:
                conn.close()

    def add_price_record(self, token_pair: str, exchange: str, price: float, 
                        volume: Optional[float] = None) -> bool:
        """Record real-time price data"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO dex_prices 
                (token_pair, dex, price, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (token_pair, exchange, price, int(time.time())))
            
            conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding price record: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def monitor_prices(self) -> None:
        """Continuous price monitoring across all configured DEXes"""
        self.logger.info("Starting price monitoring...")
        try:
            while True:
                # Get prices from all DEXes
                prices = self.dex_interface.get_all_prices()
                
                # Record prices
                for dex_name, dex_prices in prices.items():
                    for pair_name, price in dex_prices.items():
                        if price is not None:
                            self.add_price_record(
                                token_pair=pair_name,
                                exchange=dex_name,
                                price=float(price)
                            )
                
                # Check for arbitrage opportunities
                opportunities = self.dex_interface.check_arbitrage_opportunities()
                if opportunities:
                    self.logger.info(f"Found arbitrage opportunities: {opportunities}")
                
                # Sleep for configured interval
                time.sleep(0.5)  # 500ms default interval
                
        except Exception as e:
            self.logger.error(f"Error in price monitoring loop: {e}")
            raise

def main() -> None:
    """Example usage of price analyzer"""
    try:
        analyzer = PriceAnalyzer()
        analyzer.monitor_prices()
    except KeyboardInterrupt:
        print("\nPrice monitoring stopped")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
>>>>>>> 245fdac14b0b9bc65ffd42e3056011a2ab2b4d30
