"""
Simulated market data provider for testing and development
"""
import time
import random
import math
from typing import Dict, List, Any
from .base_provider import BaseDataProvider


class SimulatedDataProvider(BaseDataProvider):
    """Provides simulated market data with realistic patterns"""
    
    def __init__(self) -> None:
        """Initialize simulated data provider"""
        self.last_update = time.time()
        self.base_prices = {
            'ETH': 2000.0,
            'BTC': 35000.0,
            'USDC': 1.0,
            'DAI': 1.0,
            'LINK': 15.0
        }
        self.volatility = {
            'ETH': 0.02,
            'BTC': 0.015,
            'USDC': 0.001,
            'DAI': 0.001,
            'LINK': 0.025
        }
        self.price_history: Dict[str, List[Dict[str, Any]]] = {
            token: [{'timestamp': time.time(), 'value': price, 'uniswap': price, 'sushiswap': price * 0.999}] 
            for token, price in self.base_prices.items()
        }
        self.trends = {
            token: random.choice([-1, 1]) for token in self.base_prices
        }
        
    def _update_prices(self) -> None:
        """Update simulated prices with realistic movements"""
        current_time = time.time()
        elapsed = current_time - self.last_update
        
        # Update prices every 5 seconds
        if elapsed >= 5:
            for token in self.base_prices:
                # Random walk with trend
                trend = self.trends[token]
                if random.random() < 0.1:  # 10% chance to change trend
                    self.trends[token] = -trend
                
                # Calculate price movement
                volatility = self.volatility[token]
                movement = random.gauss(0, volatility) + (trend * volatility * 0.5)
                current_price = self.price_history[token][-1]['value']
                new_price = current_price * (1 + movement)
                
                # Ensure stable coins stay close to $1
                if token in ['USDC', 'DAI']:
                    new_price = max(0.99, min(1.01, new_price))
                
                # Add slight variation between DEXes
                uniswap_price = new_price
                sushiswap_price = new_price * (1 + random.uniform(-0.002, 0.002))
                
                self.price_history[token].append({
                    'timestamp': current_time,
                    'value': new_price,
                    'uniswap': uniswap_price,
                    'sushiswap': sushiswap_price
                })
                
                if len(self.price_history[token]) > 100:
                    self.price_history[token].pop(0)
            
            self.last_update = current_time
    
    def get_market_data(self) -> Dict[str, Any]:
        """Get current market analysis data"""
        self._update_prices()
        
        # Calculate overall market trend
        price_changes = []
        for token in self.base_prices:
            if len(self.price_history[token]) >= 2:
                change = (self.price_history[token][-1]['value'] / self.price_history[token][-2]['value']) - 1
                price_changes.append(change)
        
        avg_change = sum(price_changes) / len(price_changes) if price_changes else 0
        trend = 'bullish' if avg_change > 0.001 else 'bearish' if avg_change < -0.001 else 'neutral'
        
        # Calculate volatility
        volatility = math.sqrt(sum(x * x for x in price_changes) / len(price_changes)) if price_changes else 0
        
        # Generate opportunity score based on volatility and price movements
        opportunity_score = min(100, max(0, 50 + (volatility * 1000) + (avg_change * 200)))
        
        # Current prices for all tokens
        current_prices = {
            token: history[-1]['value'] for token, history in self.price_history.items()
        }
        
        # Generate volatility data
        volatility_data = []
        for token in self.base_prices:
            history = self.price_history[token]
            for entry in history[-20:]:  # Last 20 data points
                volatility_data.append({
                    'timestamp': entry['timestamp'],
                    'value': abs((entry['value'] / history[0]['value'] - 1) * 100)
                })
        
        # Generate liquidity data
        liquidity_data = []
        base_liquidity = 1000000  # $1M base liquidity
        for slip in [0.001, 0.005, 0.01, 0.02, 0.05]:
            liquidity_data.append({
                'level': f"{slip * 100}%",
                'value': round(base_liquidity * math.exp(-10 * slip), 2)
            })
        
        return {
            'prices': current_prices,
            'price_history': [
                {
                    'timestamp': entry['timestamp'],
                    'uniswap': entry['uniswap'],
                    'sushiswap': entry['sushiswap']
                }
                for entry in self.price_history['ETH'][-20:]  # Last 20 data points
            ],
            'volatility': volatility_data,
            'liquidity': liquidity_data,
            'trend': trend,
            'opportunity_score': round(opportunity_score),
            'gas_price': random.randint(25, 35),
            'gas_trend': random.choice(['rising', 'falling', 'stable']),
            'network_congestion': random.choice(['low', 'normal', 'high'])
        }
    
    def get_price_history(self, token: str) -> List[Dict[str, Any]]:
        """Get price history for a token"""
        self._update_prices()
        return self.price_history.get(token, [])
    
    def get_liquidity_data(self) -> Dict[str, List[Any]]:
        """Get liquidity depth data"""
        depths = []
        base_liquidity = 1000000  # $1M base liquidity
        
        # Generate realistic liquidity curve
        for slip in [0.001, 0.005, 0.01, 0.02, 0.05]:  # 0.1%, 0.5%, 1%, 2%, 5%
            # Liquidity typically decreases exponentially with slippage
            liquidity = base_liquidity * math.exp(-10 * slip)
            depths.append(round(liquidity, 2))
        
        return {
            'depths': depths,
            'slippage_levels': [0.1, 0.5, 1.0, 2.0, 5.0]
        }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        base_gas = random.randint(25, 35)
        return {
            'gas_price': base_gas,
            'gas_trend': random.choice(['rising', 'falling', 'stable']),
            'network_congestion': random.choice(['low', 'normal', 'high']),
            'block_time': round(random.uniform(12, 14), 1),
            'pending_transactions': random.randint(10, 100),
            'priority_fee': round(base_gas * 0.1, 1)
        }
