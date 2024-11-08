import logging
from typing import Dict, List, Union, TypeVar, Any, Optional, cast
from web3 import Web3
from web3.types import Wei
import json
from time import time

logger = logging.getLogger(__name__)

# Set module-level logging to INFO by default
logger.setLevel(logging.INFO)

T = TypeVar('T')
Opportunity = Dict[str, Union[str, float, bool]]


class AdvancedArbitrageDetector:
    def __init__(self, networks: List[str], w3_connections: Dict[str, Web3], config: Dict[str, Any]) -> None:
        self.networks = networks
        self.w3_connections = w3_connections
        self.config = config
        self.min_profit_threshold = float(config.get('MIN_PROFIT_THRESHOLD', 0.01))
        self.max_slippage = float(config.get('MAX_SLIPPAGE', 0.01))
        self.last_no_path_log = 0.0  # Track last time we logged no path found
        self.no_path_count = 0  # Track count of no paths found
        self.last_token_check: Dict[str, float] = dict()  # Track last check time per token
        self.check_interval = 30  # Minimum seconds between checks per token

        # Initialize PathFinder contract
        self.w3_sepolia: Optional[Web3] = w3_connections.get('Ethereum Sepolia')
        self.pathfinder = None

        if self.w3_sepolia:
            try:
                with open('abi/PathFinder.json', 'r') as f:
                    pathfinder_abi = json.load(f)
                self.pathfinder_address = Web3.to_checksum_address(config.get('PATHFINDER_ADDRESS', ''))
                self.pathfinder = self.w3_sepolia.eth.contract(
                    address=self.pathfinder_address,
                    abi=pathfinder_abi
                )
                logger.info(f"PathFinder contract initialized at {self.pathfinder_address}")
            except Exception as e:
                logger.error(f"Error initializing PathFinder contract: {e}")

    def _get_gas_price(self) -> Wei:
        """Get current gas price with type checking"""
        assert self.w3_sepolia is not None, "Web3 connection not initialized"
        base_gas_price = Wei(self.w3_sepolia.eth.gas_price)
        # Use a much lower gas price for Sepolia testing
        return Wei(int(base_gas_price * 0.5))  # 50% of current gas price

    def _get_block_timestamp(self) -> float:
        """Get latest block timestamp with type checking"""
        assert self.w3_sepolia is not None, "Web3 connection not initialized"
        return float(self.w3_sepolia.eth.get_block('latest')['timestamp'])

    def _should_check_token(self, token: str) -> bool:
        """Determine if enough time has passed to check this token again"""
        current_time = time()
        last_check = self.last_token_check.get(token, 0)
        if current_time - last_check >= self.check_interval:
            self.last_token_check[token] = current_time
            return True
        return False

    def _log_no_path_found(self, token: str, amount: Wei) -> None:
        """Handle logging of no path found cases with rate limiting"""
        self.no_path_count += 1
        current_time = time()

        # Only log every 30 seconds and only if we have accumulated some no-path cases
        if current_time - self.last_no_path_log >= 30 and self.no_path_count > 0:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"No profitable paths found in last 30s: {self.no_path_count} attempts")
            self.last_no_path_log = current_time
            self.no_path_count = 0

    def detect_arbitrage(self, token_prices: Dict[str, Dict[str, float]], gas_prices: Dict[str, float]) -> List[Opportunity]:
        """Detect arbitrage opportunities using the PathFinder contract"""
        opportunities: List[Opportunity] = []

        try:
            if not self.pathfinder or not self.w3_sepolia:
                logger.error("PathFinder contract not initialized")
                return []

            # Get current gas price
            gas_price = self._get_gas_price()

            # Get supported tokens from config
            tokens = self.config.get('SUPPORTED_TOKENS', [])
            if not tokens:
                logger.error("No supported tokens configured")
                return []

            # Convert tokens to list if it's a numpy array
            if not isinstance(tokens, list):
                tokens = list(tokens)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Checking paths for tokens: {tokens}")

            # Try smaller amounts for Sepolia testing
            test_amounts = [
                Wei(Web3.to_wei(0.001, 'ether')),  # 0.001 ETH
                Wei(Web3.to_wei(0.002, 'ether')),  # 0.002 ETH
                Wei(Web3.to_wei(0.005, 'ether'))   # 0.005 ETH
            ]

            wallet_address = Web3.to_checksum_address(self.config.get('WALLET_ADDRESS', ''))

            # Find paths for each token and amount
            for token in tokens:
                # Skip if we've checked this token too recently
                if not self._should_check_token(token):
                    continue

                token_addr = Web3.to_checksum_address(token)
                for amount in test_amounts:
                    try:
                        path = self.pathfinder.functions.findBestPath(
                            token_addr,
                            amount,
                            gas_price
                        ).call({'from': wallet_address})

                        # Convert path to opportunity if profitable
                        if path['expectedProfit'] > 0:
                            # Convert lists to strings for JSON serialization
                            path_str = ','.join([t.lower() for t in path['tokens']])
                            dexes_str = ','.join([d.lower() for d in path['dexes']])

                            opportunity: Opportunity = {
                                'type': 'Cross-Network',
                                'path': path_str,
                                'dexes': dexes_str,
                                'amount': float(Web3.from_wei(amount, 'ether')),
                                'profit': float(Web3.from_wei(path['expectedProfit'], 'ether')),
                                'gas_cost': float(Web3.from_wei(path['totalGasEstimate'] * gas_price, 'ether')),
                                'timestamp': self._get_block_timestamp(),
                                'flash_loan': bool(path['useFlashLoan'])
                            }
                            opportunities.append(opportunity)
                            logger.info(f"Found profitable opportunity: {opportunity}")

                    except Exception as e:
                        error_str = str(e)
                        if '0xbd3f5ffe' in error_str:
                            # This is an expected case when no profitable path is found
                            self._log_no_path_found(token, amount)
                        else:
                            # Log other unexpected errors
                            logger.error(f"Unexpected error finding path for token {token} with amount {Web3.from_wei(amount, 'ether')} ETH: {error_str}")
                        continue

            return sorted(opportunities, key=lambda x: float(x['profit']), reverse=True)

        except Exception as e:
            logger.error(f"Error in detect_arbitrage: {e}")
            return []

    def validate_opportunity(self, opportunity: Opportunity) -> bool:
        """Validate if an arbitrage opportunity is still valid"""
        try:
            if not self.pathfinder or not self.w3_sepolia:
                return False

            # Get current gas price
            gas_price = self._get_gas_price()

            # Convert path string back to list
            path_list = cast(str, opportunity['path']).split(',')
            if not path_list:
                return False

            wallet_address = Web3.to_checksum_address(self.config.get('WALLET_ADDRESS', ''))

            # Call findBestPath with the first token in the path
            path = self.pathfinder.functions.findBestPath(
                Web3.to_checksum_address(path_list[0]),
                Wei(Web3.to_wei(opportunity['amount'], 'ether')),
                gas_price
            ).call({'from': wallet_address})

            # Check if profit still exists
            current_profit = float(Web3.from_wei(path['expectedProfit'], 'ether'))
            if current_profit < float(opportunity['profit']) * (1 - self.max_slippage):
                return False

            return True

        except Exception as e:
            error_str = str(e)
            if '0xbd3f5ffe' in error_str:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Path is no longer profitable")
            else:
                logger.error(f"Error validating opportunity: {e}")
            return False

    def estimate_execution_cost(self, opportunity: Opportunity) -> float:
        """Estimate the total cost of executing an arbitrage opportunity"""
        try:
            if not self.pathfinder or not self.w3_sepolia:
                return float('inf')

            # Get current gas price
            gas_price = self._get_gas_price()

            # Convert path string back to list
            path_list = cast(str, opportunity['path']).split(',')
            if not path_list:
                return float('inf')

            wallet_address = Web3.to_checksum_address(self.config.get('WALLET_ADDRESS', ''))

            # Call findBestPath with the first token in the path
            path = self.pathfinder.functions.findBestPath(
                Web3.to_checksum_address(path_list[0]),
                Wei(Web3.to_wei(opportunity['amount'], 'ether')),
                gas_price
            ).call({'from': wallet_address})

            # Calculate total cost in ETH
            total_cost = float(Web3.from_wei(path['totalGasEstimate'] * gas_price, 'ether'))

            return total_cost

        except Exception as e:
            error_str = str(e)
            if '0xbd3f5ffe' in error_str:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("Could not estimate cost - path no longer valid")
            else:
                logger.error(f"Error estimating execution cost: {e}")
            return float('inf')
