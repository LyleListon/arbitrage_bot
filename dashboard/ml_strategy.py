from datetime import datetime
import logging
import numpy as np
from typing import Dict, Optional, List

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class TokenVolumeTracker:
    def __init__(self):
        self._volume_cache = {}
    
    def update_volume(self, token, exchange, network, volume):
        key = f"{token}_{exchange}_{network}"
        self._volume_cache[key] = {'volume': volume, 'timestamp': datetime.now().timestamp()}
    
    def get_volume(self, token, exchange, network):
        key = f"{token}_{exchange}_{network}"
        entry = self._volume_cache.get(key)
        return entry['volume'] if entry else None

class NetworkVolatilityTracker:
    def __init__(self):
        self._volatility_cache = {}
    
    def calculate_volatility(self, token, network, prices):
        if len(prices) < 2:
            return 0.0
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(returns) * np.sqrt(len(returns))
        self._volatility_cache[f"{token}_{network}"] = {
            'volatility': volatility,
            'timestamp': datetime.now().timestamp()
        }
        return volatility

class MLOpportunityScorer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.volume_tracker = TokenVolumeTracker()
        self.volatility_tracker = NetworkVolatilityTracker()
        self.model = RandomForestClassifier(n_estimators=100) if SKLEARN_AVAILABLE else None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self._is_trained = False

    def score_opportunity(self, opportunity):
        try:
            spread_weight = 0.4
            volume_weight = 0.2
            volatility_weight = 0.2
            cost_weight = 0.2

            spread_score = min(opportunity['spread_percent'] / 5.0, 1.0)
            volume_score = min(opportunity.get('volume', 0.0) / 1000000.0, 1.0)
            volatility_score = 1.0 - min(opportunity.get('volatility', 0.0) / 0.1, 1.0)
            cost_score = 1.0 - min(opportunity.get('gas_cost', 0.0) / 0.01, 1.0)

            return float(
                spread_score * spread_weight +
                volume_score * volume_weight +
                volatility_score * volatility_weight +
                cost_score * cost_weight
            )
        except Exception as e:
            self.logger.error(f"Error scoring opportunity: {e}")
            return 0.0
