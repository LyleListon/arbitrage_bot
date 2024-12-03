"""Enhanced Price Analysis Module with Real-time Integration and Token Optimization"""

import logging
import time
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, Any, Optional, List, TypedDict, cast
from decimal import Decimal
import statistics
from .token_optimizer import TokenOptimizer

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
    def __init__(self, db_path: str = 'arbitrage_bot.db') -> None:
        self.db_path = db_path
        self.token_optimizer = TokenOptimizer(db_path)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Drop existing tables to recreate with correct schema
        self._drop_tables()
        result = self._init_database()
        
        # Initialize test data
        self._init_test_data()
    
    def _drop_tables(self) -> None:
        """Drop existing tables to recreate with correct schema"""
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS price_history')
            cursor.execute('DROP TABLE IF EXISTS opportunity_history')
            conn.commit()
        except Exception as e:
            self.logger.error(f"Error dropping tables: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def _init_database(self) -> bool:
        """Initialize database tables"""
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_pair TEXT NOT NULL,
                    exchange TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL,
                    timestamp INTEGER NOT NULL,
                    block_number INTEGER,
                    UNIQUE(token_pair, exchange, block_number)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS opportunity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_pair TEXT NOT NULL,
                    exchange_in TEXT NOT NULL,
                    exchange_out TEXT NOT NULL,
                    price_in REAL NOT NULL,
                    price_out REAL NOT NULL,
                    spread_percent REAL NOT NULL,
                    potential_profit_usd REAL NOT NULL,
                    gas_cost_usd REAL NOT NULL,
                    net_profit_usd REAL NOT NULL,
                    executed BOOLEAN DEFAULT FALSE,
                    timestamp INTEGER NOT NULL
                )
            ''')
            
            conn.commit()
            return True
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def _init_test_data(self) -> None:
        """Initialize test data for demonstration"""
        try:
            # Add some test price history
            token_pairs = ['WETH/USDC', 'WETH/DAI', 'USDC/DAI']
            exchanges = ['baseswap', 'aerodrome']
            
            current_time = int(time.time())
            for token_pair in token_pairs:
                for exchange in exchanges:
                    # Add price points for the last hour
                    for i in range(60):
                        timestamp = current_time - (i * 60)  # One point per minute
                        
                        # Generate slightly different prices for each exchange
                        base_price = {
                            'WETH/USDC': 2250.0,
                            'WETH/DAI': 2251.0,
                            'USDC/DAI': 1.001
                        }[token_pair]
                        
                        # Add some random variation
                        variation = (hash(f"{timestamp}{exchange}") % 100) / 1000.0
                        price = base_price * (1 + variation)
                        
                        self.add_price_record(
                            token_pair=token_pair,
                            exchange=exchange,
                            price=price,
                            volume=100000.0,
                            timestamp=timestamp
                        )
            
            # Add some test opportunities
            for i in range(10):
                timestamp = current_time - (i * 360)  # One opportunity every 6 minutes
                for token_pair in token_pairs:
                    spread = (hash(f"{timestamp}{token_pair}") % 100) / 1000.0
                    potential_profit = spread * 1000.0
                    gas_cost = 50.0
                    net_profit = potential_profit - gas_cost
                    
                    self.add_opportunity(
                        token_pair=token_pair,
                        exchange_in='baseswap',
                        exchange_out='aerodrome',
                        price_in=base_price * (1 - spread/2),
                        price_out=base_price * (1 + spread/2),
                        spread_percent=spread * 100,
                        potential_profit_usd=potential_profit,
                        gas_cost_usd=gas_cost,
                        net_profit_usd=net_profit
                    )
            
            self.logger.info("Test data initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing test data: {str(e)}")
    
    def get_db_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_token_price(self, dex: str, token_in: str, token_out: str, amounts_out: List[int], decimals_out: int) -> Optional[Decimal]:
        """Get token price with optimized caching and fixed WETH/DAI calculation"""
        cache_key = f"price_{dex}_{token_in}_{token_out}"
        cached_price = self.token_optimizer.retrieve(cache_key)
        
        if cached_price is not None:
            return Decimal(str(cached_price))
        else:
            price = self.calculate_token_price(dex, token_in, token_out, amounts_out, decimals_out)
            return price               
        try:
            if token_in == 'WETH' and token_out == 'DAI':
                # For WETH/DAI, convert to DAI terms and adjust for DAI/USDC ratio
                raw_price = Decimal(amounts_out[1]) / Decimal(10 ** decimals_out)
                if (dai_usdc_price := self.get_token_price(dex, 'DAI', 'USDC', amounts_out, decimals_out)):
                    # Fixed: Multiply by DAI/USDC ratio instead of dividing
                    price = raw_price * dai_usdc_price
                    self.token_optimizer.store(cache_key, str(price))
                    return price
            else:
                # Standard price calculation for other pairs
                price = Decimal(amounts_out[1]) / Decimal(10 ** decimals_out)
                self.token_optimizer.store(cache_key, str(price))
                return price
                
        except Exception as e:
            self.logger.error(f"Error calculating token price: {str(e)}")
            return None
        
        return None

    def add_price_record(self, token_pair: str, exchange: str, price: float, 
                        volume: Optional[float] = None, block_number: Optional[int] = None,
                        timestamp: Optional[int] = None) -> bool:
        conn: Optional[sqlite3.Connection] = None
        success: bool = False
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            if timestamp is None:
                timestamp = int(datetime.now().timestamp())
                
            cursor.execute('''
                INSERT OR REPLACE INTO price_history 
                (token_pair, exchange, price, volume, block_number, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (token_pair, exchange, price, volume, block_number, timestamp))
            
            conn.commit()
            
            # Cache the latest price
            cache_key = f"latest_price_{token_pair}_{exchange}"
            self.token_optimizer.store(cache_key, price)
            
            success = True
        except Exception as e:
            self.logger.error(f"Error adding price record: {str(e)}")
            success = False
        finally:
            if conn:
                conn.close()
            return success

    def add_opportunity(self, token_pair: str, exchange_in: str, exchange_out: str,
                       price_in: float, price_out: float, spread_percent: float,
                       potential_profit_usd: float, gas_cost_usd: float,
                       net_profit_usd: float) -> bool:
        conn: Optional[sqlite3.Connection] = None
        success: bool = False
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO opportunity_history 
                (token_pair, exchange_in, exchange_out, price_in, price_out, 
                spread_percent, potential_profit_usd, gas_cost_usd, net_profit_usd, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token_pair, exchange_in, exchange_out, price_in, price_out,
                spread_percent, potential_profit_usd, gas_cost_usd, net_profit_usd,
                int(datetime.now().timestamp())
            ))
            
            conn.commit()
            success = True
        except Exception as e:
            self.logger.error(f"Error recording opportunity: {str(e)}")
            success = False
        finally:
            if conn:
                conn.close()
            return success

    def get_price_statistics(self, token_pair: str, exchange: str,
                           timeframe_minutes: int = 60) -> Optional[PriceStats]:
        conn: Optional[sqlite3.Connection] = None
        try:
            cache_key = f"stats_{token_pair}_{exchange}_{timeframe_minutes}"
            cached_stats = self.token_optimizer.retrieve(cache_key)
            
            if cached_stats is not None:
                return cast(Optional[PriceStats], cached_stats)
                
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cutoff_time = int((datetime.now() - timedelta(minutes=timeframe_minutes)).timestamp())
            cursor.execute('''
                SELECT price, volume, timestamp 
                FROM price_history 
                WHERE token_pair = ? AND exchange = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            ''', (token_pair, exchange, cutoff_time))
            
            rows = cursor.fetchall()
            if not rows or len(rows) < 2:
                return None
                
            prices = [row['price'] for row in rows]
            volumes = [row['volume'] for row in rows if row['volume'] is not None]
            
            stats: PriceStats = {
                'current_price': prices[-1],
                'vwap': (sum(p * v for p, v in zip(prices, volumes)) / sum(volumes)
                        if volumes else statistics.mean(prices)),
                'mean_price': statistics.mean(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'volatility': (statistics.stdev(prices) / statistics.mean(prices)) * 100,
                'std_dev': statistics.stdev(prices),
                'samples': len(prices)
            }
            
            # Cache statistics for 5 minutes
            self.token_optimizer.store(cache_key, stats)
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating price statistics: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    def calculate_opportunity_score(self, spread_percent: float, volatility: float,
                                 net_profit_usd: float, volume: Optional[float] = None) -> float:
        try:
            base_score = min(spread_percent * 10, 50)
            volatility_score = max(0, 20 - (volatility * 2))
            profit_score = min(net_profit_usd * 5, 20)
            volume_score = min(volume / 1000, 10) if volume else 5
            
            total_score = base_score + volatility_score + profit_score + volume_score
            return min(total_score, 100)
            
        except Exception as e:
            self.logger.error(f"Error calculating opportunity score: {str(e)}")
            return 0.0

    def get_historical_performance(self, timeframe_minutes: int = 1440) -> HistoricalPerformance:
        cache_key = f"hist_perf_{timeframe_minutes}"
        cached_perf = self.token_optimizer.retrieve(cache_key)
        
        if cached_perf is not None:
            return cast(HistoricalPerformance, cached_perf)
            
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cutoff_time = int((datetime.now() - timedelta(minutes=timeframe_minutes)).timestamp())
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_opportunities,
                    AVG(spread_percent) as avg_spread,
                    AVG(net_profit_usd) as avg_profit,
                    SUM(CASE WHEN executed = 1 THEN net_profit_usd ELSE 0 END) as total_profit,
                    SUM(CASE WHEN executed = 1 THEN 1 ELSE 0 END) as executed_trades
                FROM opportunity_history 
                WHERE timestamp >= ?
            ''', (cutoff_time,))
            
            row = cursor.fetchone()
            
            performance: HistoricalPerformance = {
                'total_opportunities': int(row['total_opportunities'] or 0),
                'average_spread': float(row['avg_spread'] or 0),
                'average_profit': float(row['avg_profit'] or 0),
                'total_profit': float(row['total_profit'] or 0),
                'executed_trades': int(row['executed_trades'] or 0),
                'timeframe_minutes': timeframe_minutes
            }
            
            # Cache performance data for 5 minutes
            self.token_optimizer.store(cache_key, performance)
            return performance
            
        except Exception as e:
            self.logger.error(f"Error getting historical performance: {str(e)}")
            return {
                'total_opportunities': 0,
                'average_spread': 0.0,
                'average_profit': 0.0,
                'total_profit': 0.0,
                'executed_trades': 0,
                'timeframe_minutes': timeframe_minutes
            }
        finally:
            conn.close()
