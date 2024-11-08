"""
Base data provider interface and data structures

@CONTEXT: Core data provider definitions
@LAST_POINT: 2024-01-31 - Added comprehensive data structures
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class PairConfig:
    """Trading pair configuration"""
    base_token: str
    quote_token: str
    decimals: int
    min_profit_threshold: float
    max_slippage: float
    min_liquidity: float = 0.0
    is_active: bool = True

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    supported_pairs: List[str]
    fee_structure: Dict[str, float]
    min_order_size: Dict[str, float]
    max_order_size: Dict[str, float]
    is_active: bool = True

class BaseDataProvider:
    """Base class for data providers"""
    
    def get_market_data(self) -> Dict[str, Any]:
        """Get comprehensive market data"""
        raise NotImplementedError
        
    def get_price_history(self, base_token: str, quote_token: str, exchange: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get price history for a trading pair"""
        raise NotImplementedError
        
    def get_liquidity_data(self, base_token: str, quote_token: str, exchange: Optional[str] = None) -> Dict[str, List[float]]:
        """Get liquidity data for a trading pair"""
        raise NotImplementedError
        
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        raise NotImplementedError
        
    def add_trading_pair(self, config: PairConfig) -> bool:
        """Add a new trading pair"""
        raise NotImplementedError
        
    def add_exchange(self, config: ExchangeConfig) -> bool:
        """Add a new exchange"""
        raise NotImplementedError
        
    def get_arbitrage_opportunities(self, min_profit_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Get current arbitrage opportunities"""
        raise NotImplementedError
        
    def get_exchange_status(self, exchange: str) -> Dict[str, Any]:
        """Get exchange status"""
        raise NotImplementedError
        
    def get_supported_pairs(self, exchange: Optional[str] = None) -> List[str]:
        """Get supported trading pairs"""
        raise NotImplementedError
        
    def get_fee_estimates(self, base_token: str, quote_token: str, amount: float, exchange: Optional[str] = None) -> Dict[str, float]:
        """Get fee estimates for trades"""
        raise NotImplementedError
        
    def validate_pair_config(self, config: PairConfig) -> bool:
        """Validate trading pair configuration"""
        raise NotImplementedError
        
    def validate_exchange_config(self, config: ExchangeConfig) -> bool:
        """Validate exchange configuration"""
        raise NotImplementedError
