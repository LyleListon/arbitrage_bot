import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class MockDataGenerator:
    def __init__(self, config: Dict):
        self.config = config
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()

    def generate_price_data(self, token_pair: str) -> pd.DataFrame:
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='h')
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.1)
        return pd.DataFrame({'price': prices}, index=dates)

    def generate_volatility_data(self, token_pair: str) -> pd.DataFrame:
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        hourly_vol = np.random.rand(len(dates)) * 0.05 + 0.01
        daily_vol = np.random.rand(len(dates)) * 0.1 + 0.05
        weekly_vol = np.random.rand(len(dates)) * 0.2 + 0.1
        return pd.DataFrame({
            'hourly_volatility': hourly_vol,
            'daily_volatility': daily_vol,
            'weekly_volatility': weekly_vol
        }, index=dates)

    def generate_correlation_data(self, token_pair: str) -> pd.DataFrame:
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        dex_correlation = np.random.rand(len(dates)) * 0.4 + 0.6
        pair_correlation = np.random.rand(len(dates)) * 0.4 + 0.6
        strength = np.random.rand(len(dates)) * 0.5 + 0.5
        return pd.DataFrame({
            'dex_correlation': dex_correlation,
            'pair_correlation': pair_correlation,
            'strength': strength
        }, index=dates)

    def generate_market_data(self, token_pair: str) -> pd.DataFrame:
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='h')
        spread = np.random.rand(len(dates)) * 0.01 + 0.001
        volume = np.random.randint(1000, 100000, size=len(dates))
        liquidity = np.random.randint(100000, 10000000, size=len(dates))
        return pd.DataFrame({
            'spread': spread,
            'volume': volume,
            'liquidity': liquidity
        }, index=dates)

    def generate_opportunity_data(self, token_pair: str) -> List[Dict]:
        num_opportunities = np.random.randint(5, 20)
        opportunities = []
        for _ in range(num_opportunities):
            timestamp = self.start_date + timedelta(seconds=np.random.randint(0, int((self.end_date - self.start_date).total_seconds())))
            opportunities.append({
                'token0': token_pair.split('/')[0],
                'token1': token_pair.split('/')[1],
                'prediction': {
                    'price_prediction': np.random.rand() * 10 + 100,
                    'opportunity_probability': np.random.rand() * 0.3 + 0.7,
                    'spread_prediction': np.random.rand() * 0.01 + 0.001,
                    'confidence': np.random.rand() * 0.2 + 0.8
                },
                'timestamp': timestamp.isoformat()
            })
        return opportunities

    def generate_model_metrics(self) -> pd.DataFrame:
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='D')
        lstm_mae = np.random.rand(len(dates)) * 0.1 + 0.9
        rf_accuracy = np.random.rand(len(dates)) * 0.1 + 0.8
        xgb_r2 = np.random.rand(len(dates)) * 0.1 + 0.7
        return pd.DataFrame({
            'LSTM MAE': lstm_mae,
            'RF Accuracy': rf_accuracy,
            'XGB R2': xgb_r2
        }, index=dates)

    def generate_all_data(self, token_pair: str) -> Dict[str, pd.DataFrame]:
        return {
            'price_data': self.generate_price_data(token_pair),
            'volatility_data': self.generate_volatility_data(token_pair),
            'correlation_data': self.generate_correlation_data(token_pair),
            'market_data': self.generate_market_data(token_pair),
            'opportunities': self.generate_opportunity_data(token_pair),
            'model_metrics': self.generate_model_metrics()
        }
