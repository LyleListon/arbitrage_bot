"nk ""Real-time Price Analysis Module with DEX Integration"""

import logging
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

class PriceStats(TypedDict):
    current_price: float
    vwap: float
    mean_price: float
    min_price: float
    max_price: float
    volatility: float
    std_dev: float
    samples: int

class HistoricalPerformance(TypedDict):
    total_opportunities: int
    average_spread: float
    average_profit: float
    total_profit: float
    executed_trades: int
    timeframe_minutes: int

class PriceAnalyzer:
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
            return None
        finally:
            if conn:
                conn.close()

    def get_historical_performance(self, timeframe_minutes: int = 1440) -> HistoricalPerformance:
        """Get historical performance metrics"""
        conn = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
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
