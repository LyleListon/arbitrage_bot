iawwaddmport logging
from typing import Dict, Any, List, Optional, Tuple, TypeVar, cast
from web3 import Web3
from datetime import datetime
import json
import threading
import time
from dashboard.blockchain_monitor import BlockchainMonitor

logger = logging.getLogger(__name__)

# Define a Contract type
Contract = TypeVar('Contract')


class ContractMonitor:
    def __init__(self, w3: Web3, contract_address: str) -> None:
        self.w3 = w3
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.trades: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        self.contract = self.load_contract()
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.blockchain_monitor = BlockchainMonitor(w3, contract_address)
        logger.info(f"Contract monitor initialized for {contract_address}")

    def load_contract(self) -> Optional[Contract]:
        """Load ABI from file"""
        try:
            with open('abi/ArbitrageFactory.json', 'r') as abi_file:
                contract_abi = json.load(abi_file)
            contract = self.w3.eth.contract(address=self.contract_address, abi=contract_abi)

            # Test if contract is accessible
            try:
                contract.functions.getComponents().call()
                return contract
            except Exception as e:
                logger.error(f"Contract not accessible: {e}")
                return None

        except Exception as e:
            logger.error(f"Error loading contract ABI: {e}")
            return None

    def start_monitoring(self, poll_interval: int = 2) -> None:
        """Start monitoring in a separate thread"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(poll_interval,))
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logger.info("Contract monitoring started")

    def stop_monitoring(self) -> None:
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
            logger.info("Contract monitoring stopped")

    def _monitor_loop(self, poll_interval: int) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                # Get real blockchain transactions
                transactions = self.blockchain_monitor.get_transactions()

                # Only update if we have new transactions
                if transactions and transactions != self.trades:
                    self.trades = transactions
                    logger.info(f"Found {len(self.trades)} transactions")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            time.sleep(poll_interval)

    def get_components(self) -> Optional[Tuple[List[str], List[str]]]:
        """Get current component addresses"""
        try:
            if not self.contract:
                # Try to reload contract
                self.contract = self.load_contract()
                if not self.contract:
                    return None

            # Get components
            result = self.contract.functions.getComponents().call()
            if not result or len(result) != 2:
                logger.error("Invalid components result")
                return None

            addresses, names = result
            if not addresses or not names or len(addresses) != len(names):
                logger.error("Mismatched components arrays")
                return None

            return cast(Tuple[List[str], List[str]], result)

        except Exception as e:
            logger.error(f"Error getting components: {e}")
            return None

    def get_total_trades(self) -> int:
        """Get total number of transactions"""
        return len(self.trades)

    def get_success_rate(self) -> float:
        """Get success rate of transactions"""
        if not self.trades:
            return 0
        successful = sum(1 for trade in self.trades if trade['success'])
        return (successful / len(self.trades)) * 100

    def get_average_roi(self) -> float:
        """Get average ROI across all transactions"""
        if not self.trades:
            return 0
        stats = self.blockchain_monitor.get_profit_stats()
        return stats['net_profit']

    def get_profit_history(self) -> List[Dict[str, Any]]:
        """Get historical profit data"""
        if not self.trades:
            return []

        # Group trades by hour
        history = []
        current_time = self.start_time
        one_hour = 3600  # seconds in an hour

        while current_time <= datetime.now():
            current_ts = int(current_time.timestamp())
            next_ts = current_ts + one_hour

            hour_trades = [t for t in self.trades if t['timestamp'] >= current_ts and t['timestamp'] < next_ts]

            if hour_trades:
                profit = sum(t['value'] - t['cost'] for t in hour_trades if t['success'])
                history.append({
                    'timestamp': current_ts,
                    'profit': profit
                })
            current_time = datetime.fromtimestamp(next_ts)

        return history


def init_contract_monitoring(w3: Optional[Web3], contract_address: Optional[str]) -> Optional[ContractMonitor]:
    """Initialize contract monitoring"""
    if not w3 or not contract_address:
        logger.error("Missing Web3 or contract address")
        return None

    try:
        monitor = ContractMonitor(w3, contract_address)
        monitor.start_monitoring()
        logger.info("Contract monitoring initialized and started")
        return monitor
    except Exception as e:
        logger.error(f"Error initializing contract monitoring: {e}")
        return None
