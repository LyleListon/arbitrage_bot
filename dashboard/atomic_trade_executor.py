import logging
from typing import Dict, Any
from web3 import Web3
import json


logger = logging.getLogger(__name__)


class AtomicTradeExecutor:
    def __init__(self, networks: Dict[str, Web3], config: Dict[str, Any]):
        self.networks = networks
        self.config = config
        self.slippage_tolerance = config.get('slippage_tolerance', 0.005)  # Default 0.5% slippage tolerance

        # Initialize MultiPathArbitrage contract
        try:
            with open('abi/MultiPathArbitrage.json', 'r') as f:
                self.arbitrage_abi = json.load(f)

            self.arbitrage_address = Web3.to_checksum_address("0x1A1E8924a4513899931EE4a737629335d22aDA8F")
            self.arbitrage_contract = self.networks['Ethereum Sepolia'].eth.contract(
                address=self.arbitrage_address,
                abi=self.arbitrage_abi
            )
            logger.info(f"MultiPathArbitrage contract initialized at {self.arbitrage_address}")
        except Exception as e:
            logger.error(f"Error initializing MultiPathArbitrage contract: {e}")
            raise

    def execute_atomic_trade(self, opportunity: Dict[str, Any], gas_prices: Dict[str, float]) -> bool:
        logger.info(f"Attempting to execute atomic multi-hop trade: {opportunity}")

        if not self._validate_atomic_opportunity(opportunity, gas_prices):
            logger.warning("Atomic trade validation failed. Aborting execution.")
            return False

        try:
            # Convert path to contract parameters
            path = self._convert_path_to_contract_params(opportunity)

            # Get gas price
            gas_price = self.networks['Ethereum Sepolia'].eth.gas_price

            # Estimate gas
            try:
                gas_estimate = self.arbitrage_contract.functions.executeMultiPathArbitrage(
                    path,
                    Web3.to_wei(opportunity['amount'], 'ether')
                ).estimate_gas()
                logger.info(f"Estimated gas: {gas_estimate}")
            except Exception as e:
                logger.error(f"Gas estimation failed: {e}")
                return False

            # Execute trade
            tx = self.arbitrage_contract.functions.executeMultiPathArbitrage(
                path,
                Web3.to_wei(opportunity['amount'], 'ether')
            ).build_transaction({
                'from': self.config['WALLET_ADDRESS'],
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': gas_price,
                'nonce': self.networks['Ethereum Sepolia'].eth.get_transaction_count(self.config['WALLET_ADDRESS'])
            })

            # Sign and send transaction
            signed_tx = self.networks['Ethereum Sepolia'].eth.account.sign_transaction(
                tx,
                private_key=self.config['PRIVATE_KEY']
            )
            tx_hash = self.networks['Ethereum Sepolia'].eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for transaction confirmation
            receipt = self.networks['Ethereum Sepolia'].eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] == 1:
                logger.info(f"Trade executed successfully! Tx hash: {tx_hash.hex()}")
                return True
            else:
                logger.error(f"Trade failed! Tx hash: {tx_hash.hex()}")
                return False

        except Exception as e:
            logger.error(f"Error during atomic trade execution: {e}")
            return False

    def _validate_atomic_opportunity(self, opportunity: Dict[str, Any], gas_prices: Dict[str, float]) -> bool:
        try:
            # Basic validation
            if not opportunity.get('path') or not opportunity.get('amount'):
                logger.error("Invalid opportunity format")
                return False

            # Check if amount exceeds max trade size
            max_trade_size = Web3.to_wei(10, 'ether')  # 10 ETH max trade size
            if Web3.to_wei(opportunity['amount'], 'ether') > max_trade_size:
                logger.error("Trade size exceeds maximum")
                return False

            # Validate expected profit
            min_profit = Web3.to_wei(0.001, 'ether')  # 0.001 ETH minimum profit
            if Web3.to_wei(opportunity['profit'], 'ether') < min_profit:
                logger.error("Insufficient profit")
                return False

            return True

        except Exception as e:
            logger.error(f"Error during opportunity validation: {e}")
            return False

    def _convert_path_to_contract_params(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Convert opportunity path to contract parameters"""
        try:
            steps = []
            for i in range(len(opportunity['path']) - 1):
                step = {
                    'path': [
                        Web3.to_checksum_address(opportunity['path'][i]),
                        Web3.to_checksum_address(opportunity['path'][i + 1])
                    ],
                    'dex': Web3.to_checksum_address(opportunity['dexes'][i]),
                    'minOutput': Web3.to_wei(opportunity['amount'] * (1 - self.slippage_tolerance), 'ether')
                }
                steps.append(step)

            return {
                'steps': steps,
                'totalGasEstimate': 0,  # Will be calculated by contract
                'expectedProfit': Web3.to_wei(opportunity['profit'], 'ether'),
                'useFlashLoan': opportunity.get('flash_loan', False),
                'tokens': [Web3.to_checksum_address(t) for t in opportunity['path']],
                'dexes': [Web3.to_checksum_address(d) for d in opportunity['dexes']]
            }

        except Exception as e:
            logger.error(f"Error converting path to contract params: {e}")
            raise
