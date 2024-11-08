"""
Price Trend Analysis Module
Analyzes price trends and provides insights for arbitrage opportunities
"""

import numpy as np
from scipy import stats
import logging
from datetime import datetime, timedelta
import sqlite3


class PriceAnalyzer:
    def __init__(self, db_path='arbitrage_bot.db'):
        """Initialize price analyzer with database connection"""
        self.db_path = db_path
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def get_db_connection(self):
        """Create a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_price_record(self, token, price, timestamp=None):
        """Add a new price record to the database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create price_history table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT NOT NULL,
                    price REAL NOT NULL,
                    timestamp INTEGER NOT NULL
                )
            ''')
            
            if timestamp is None:
                timestamp = int(datetime.now().timestamp())
                
            cursor.execute('''
                INSERT INTO price_history (token, price, timestamp)
                VALUES (?, ?, ?)
            ''', (token, price, timestamp))
            
            conn.commit()
            self.logger.info(f"Added price record for {token}: ${price:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error adding price record: {str(e)}")
        finally:
            conn.close()

    def calculate_trend(self, token, timeframe_minutes=60):
        """Calculate price trend over specified timeframe"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get price data for specified timeframe
            cutoff_time = int((datetime.now() - timedelta(minutes=timeframe_minutes)).timestamp())
            cursor.execute('''
                SELECT price, timestamp 
                FROM price_history 
                WHERE token = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            ''', (token, cutoff_time))
            
            rows = cursor.fetchall()
            if not rows:
                return None
                
            prices = [row['price'] for row in rows]
            timestamps = [row['timestamp'] for row in rows]
            
            if len(prices) < 2:
                return None
                
            # Calculate trend
            slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, prices)
            
            # Calculate percentage change
            price_change = ((prices[-1] - prices[0]) / prices[0]) * 100
            
            # Calculate volatility (standard deviation)
            volatility = np.std(prices)
            
            return {
                'slope': slope,
                'r_squared': r_value ** 2,
                'price_change_percent': price_change,
                'volatility': volatility,
                'current_price': prices[-1],
                'samples': len(prices)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trend: {str(e)}")
            return None
        finally:
            conn.close()

    def get_opportunity_score(self, token_in, token_out):
        """Calculate opportunity score based on price trends"""
        try:
            # Get trends for both tokens
            trend_in = self.calculate_trend(token_in)
            trend_out = self.calculate_trend(token_out)
            
            if not trend_in or not trend_out:
                return None
                
            # Calculate opportunity score based on:
            # 1. Price trends (slope difference)
            # 2. Volatility
            # 3. R-squared values (confidence in trends)
            
            slope_diff = trend_out['slope'] - trend_in['slope']
            avg_volatility = (trend_in['volatility'] + trend_out['volatility']) / 2
            avg_r_squared = (trend_in['r_squared'] + trend_out['r_squared']) / 2
            
            # Normalize factors
            norm_slope_diff = np.tanh(slope_diff)  # Between -1 and 1
            norm_volatility = 1 / (1 + avg_volatility)  # Higher volatility = lower score
            
            # Calculate final score (0-100)
            score = (
                (norm_slope_diff + 1) * 50 *  # Convert -1,1 to 0,100
                avg_r_squared *  # Weight by confidence
                norm_volatility  # Adjust for volatility risk
            )
            
            return {
                'score': score,
                'confidence': avg_r_squared * 100,
                'risk_level': 'High' if avg_volatility > 0.02 else 'Medium' if avg_volatility > 0.01 else 'Low',
                'details': {
                    'token_in': trend_in,
                    'token_out': trend_out
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating opportunity score: {str(e)}")
            return None

    def get_recent_opportunities(self, min_score=50):
        """Get recent trading opportunities above minimum score"""
        try:
            opportunities = []
            # Updated token pairs to include all combinations of supported tokens
            token_pairs = [
                # Stablecoin pairs
                ('USDC', 'DAI'),
                # ETH pairs
                ('WETH', 'USDC'),
                ('WETH', 'DAI'),
                ('WETH', 'WBTC'),
                ('WETH', 'LINK'),
                # BTC pairs
                ('WBTC', 'USDC'),
                ('WBTC', 'DAI'),
                ('WBTC', 'LINK'),
                # LINK pairs
                ('LINK', 'USDC'),
                ('LINK', 'DAI')
            ]
            
            for token_in, token_out in token_pairs:
                score = self.get_opportunity_score(token_in, token_out)
                if score and score['score'] >= min_score:
                    opportunities.append({
                        'token_in': token_in,
                        'token_out': token_out,
                        'score': score
                    })
            
            return sorted(opportunities, key=lambda x: x['score']['score'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error getting recent opportunities: {str(e)}")
            return []
