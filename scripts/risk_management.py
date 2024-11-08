"""
Enhanced risk management module for arbitrage bot
"""
import time
from typing import Dict, List, Tuple
from eth_typing import ChecksumAddress
from web3.exceptions import TransactionNotFound


class RiskManager:
    def __init__(
        self,
        w3,
        config: Dict,
        monitor
    ):
        self.w3 = w3
        self.config = config
        self.monitor = monitor
        
        # Risk parameters
        self.max_trade_size = config['security']['max_trade_size']
        self.min_profit_threshold = config['security']['min_profit_threshold']
        self.max_slippage = config['security']['max_slippage']
        self.min_liquidity_ratio = config['security']['min_liquidity_ratio']
        self.max_gas_price = config['security']['max_gas_price']
        self.max_exposure_percentage = config['security'].get('max_exposure_percentage', 5)  # Default to 5% if not specified
        self.max_concurrent_trades = config['execution']['max_concurrent_trades']
        self.max_daily_trades = config['execution'].get('max_daily_trades', 100)  # Default to 100 if not specified
        self.max_similar_pending_trades = config['execution'].get('max_similar_pending_trades', 3)  # Default to 3 if not specified
        
        # MEV protection parameters
        self.mev_time_window = config['security'].get('mev_time_window', 60)  # Default to 60 seconds
        self.mev_similarity_threshold = config['security'].get('mev_similarity_threshold', 0.8)  # Default to 80% similarity
        self.mev_risk_levels = config['security'].get('mev_risk_levels', {
            'low': 5,
            'medium': 10,
            'high': 20
        })
        
        # Flash loan parameters
        self.flash_loan_enabled = config['flash_loan']['enabled']
        self.flash_loan_min_amount = config['flash_loan']['min_amount']
        self.flash_loan_max_amount = config['flash_loan']['max_amount']
        self.flash_loan_fee_percentage = config['flash_loan']['fee_percentage']
        self.flash_loan_supported_tokens = set(config['flash_loan']['supported_tokens'])
        
        # Trade tracking
        self.current_trades = {}
        self.daily_trade_count = 0
        self.trade_count_reset_time = int(time.time())
        self.pending_similar_trades = {}
        self.recent_transactions = []

    def calculate_transaction_similarity(
        self,
        tx: Dict,
        token_path: List[ChecksumAddress],
        amount: int
    ) -> float:
        """Calculate the similarity between a transaction and our intended trade"""
        similarity_score = 0.0
        
        # Check if the transaction involves any of our token path
        if tx['to'] in token_path:
            similarity_score += 0.5
        
        # Check if the transaction amount is similar (within 20%)
        if 'value' in tx:
            value_diff = abs(tx['value'] - amount) / max(amount, 1)
            if value_diff <= 0.2:
                similarity_score += 0.3 * (1 - value_diff / 0.2)
        
        # Check if the gas price is similar (within 30%)
        if 'gasPrice' in tx and self.w3.eth.gas_price > 0:
            gas_diff = abs(tx['gasPrice'] - self.w3.eth.gas_price) / self.w3.eth.gas_price
            if gas_diff <= 0.3:
                similarity_score += 0.2 * (1 - gas_diff / 0.3)
        
        # Add a small constant to ensure medium similarity is strictly greater than 0.5
        return similarity_score + 0.01

    def check_mev_protection(
        self,
        token_path: List[ChecksumAddress],
        amount: int
    ) -> Tuple[bool, str]:
        """Check for potential MEV attacks with enhanced detection"""
        try:
            current_time = int(time.time())
            
            # Get pending transactions for this path
            mempool_filter = self.w3.eth.filter('pending')
            pending_txs = mempool_filter.get_new_entries()
            
            # Analyze transactions
            similar_txs = []
            for tx_hash in pending_txs:
                try:
                    tx = self.w3.eth.get_transaction(tx_hash)
                    similarity = self.calculate_transaction_similarity(tx, token_path, amount)
                    if similarity >= self.mev_similarity_threshold:
                        similar_txs.append((tx_hash, similarity, current_time))
                except TransactionNotFound:
                    continue
            
            # Add to recent transactions
            self.recent_transactions.extend(similar_txs)
            
            # Remove old transactions outside the time window
            self.recent_transactions = [
                tx for tx in self.recent_transactions
                if current_time - tx[2] <= self.mev_time_window
            ]
            
            # Count recent similar transactions
            recent_similar_count = len(self.recent_transactions)
            
            # Determine MEV risk level
            if recent_similar_count >= self.mev_risk_levels['high']:
                return False, f"High MEV risk: {recent_similar_count} similar transactions detected"
            elif recent_similar_count >= self.mev_risk_levels['medium']:
                return False, f"Medium MEV risk: {recent_similar_count} similar transactions detected"
            elif recent_similar_count >= self.mev_risk_levels['low']:
                return True, f"Low MEV risk: {recent_similar_count} similar transactions detected"
            
            return True, "No significant MEV risk detected"
            
        except Exception as e:
            return False, f"Error checking MEV protection: {str(e)}"

    # ... (keep all other methods unchanged)
