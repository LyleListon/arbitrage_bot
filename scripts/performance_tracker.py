"""
Performance tracking module for the Arbitrage Bot
"""
from typing import Dict, List
import time

class PerformanceTracker:
    def __init__(self):
        self.trades: List[Dict] = []
        self.daily_profits: Dict[str, float] = {}

    def add_trade(self, trade: Dict):
        self.trades.append(trade)
        trade_date = time.strftime("%Y-%m-%d", time.localtime(trade['timestamp']))
        self.daily_profits[trade_date] = self.daily_profits.get(trade_date, 0) + trade['profit']

    def get_total_profit(self) -> float:
        return sum(trade['profit'] for trade in self.trades)

    def get_average_profit(self) -> float:
        if not self.trades:
            return 0
        return self.get_total_profit() / len(self.trades)

    def get_daily_profit_trend(self) -> Dict[str, float]:
        return self.daily_profits

    def get_most_profitable_pair(self) -> str:
        if not self.trades:
            return "No trades yet"
        pair_profits = {}
        for trade in self.trades:
            pair = trade['pair']
            pair_profits[pair] = pair_profits.get(pair, 0) + trade['profit']
        return max(pair_profits, key=pair_profits.get)

    def get_performance_report(self) -> Dict:
        return {
            'total_trades': len(self.trades),
            'total_profit': self.get_total_profit(),
            'average_profit_per_trade': self.get_average_profit(),
            'daily_profit_trend': self.get_daily_profit_trend(),
            'most_profitable_pair': self.get_most_profitable_pair(),
        }
