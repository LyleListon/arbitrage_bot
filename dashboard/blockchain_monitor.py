import logging
from typing import Dict, Any, List
from web3 import Web3
from eth_typing import ChecksumAddress
import json

logger = logging.getLogger(__name__)


class BlockchainMonitor:
    def __init__(self, w3: Web3, contract_address: str) -> None:
        self.w3 = w3
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.last_block = 0
        self.transactions: List[Dict[str, Any]] = []

        # Initialize MultiPathArbitrage contract
        try:
            with open('abi/MultiPathArbitrage.json', 'r') as f:
                contract_abi = json.load(f)
            self.contract = w3.eth.contract(
                address=self.contract_address,
                abi=contract_abi
            )
            logger.info(f"Monitoring MultiPathArbitrage at {self.contract_address}")
        except Exception as e:
            logger.error(f"Error initializing contract: {e}")
            self.contract = None

    def get_transactions(self) -> List[Dict[str, Any]]:
        """Get real transactions from the blockchain"""
        try:
            current_block = self.w3.eth.block_number

            if self.last_block == 0:
                self.last_block = current_block - 1000  # Start from last 1000 blocks

            # Get new blocks
            for block_num in range(self.last_block + 1, current_block + 1):
                block = self.w3.eth.get_block(block_num, full_transactions=True)

                # Filter transactions involving our contract
                for tx in block['transactions']:
                    if isinstance(tx, dict):  # Full transaction object
                        to_addr = Web3.to_checksum_address(tx.get('to', '0x0')) if tx.get('to') else '0x0'
                        from_addr = Web3.to_checksum_address(tx.get('from', '0x0'))

                        # Check if transaction involves our contract
                        if to_addr == self.contract_address or from_addr == self.contract_address:
                            # Get transaction receipt for gas used
                            receipt = self.w3.eth.get_transaction_receipt(tx['hash'])

                            # Calculate actual cost
                            gas_used = receipt['gasUsed']
                            gas_price = tx['gasPrice']
                            cost = Web3.from_wei(gas_used * gas_price, 'ether')

                            # Get timestamp
                            block_timestamp = block['timestamp']

                            # Check if this was an arbitrage execution
                            is_arbitrage = False
                            profit = 0.0
                            try:
                                # Look for ArbitrageExecuted event
                                for log in receipt['logs']:
                                    if log['address'].lower() == self.contract_address.lower():
                                        event = self.contract.events.ArbitrageExecuted().process_log(log)
                                        if event:
                                            is_arbitrage = True
                                            profit = Web3.from_wei(event['args']['profit'], 'ether')
                                            break
                            except Exception as e:
                                logger.error(f"Error processing logs: {e}")

                            transaction = {
                                'hash': tx['hash'].hex(),
                                'from': from_addr,
                                'to': to_addr,
                                'value': Web3.from_wei(tx['value'], 'ether'),
                                'gas_used': gas_used,
                                'gas_price': Web3.from_wei(gas_price, 'gwei'),
                                'cost': cost,
                                'timestamp': block_timestamp,
                                'block': block_num,
                                'success': receipt['status'] == 1,
                                'is_arbitrage': is_arbitrage,
                                'profit': profit
                            }

                            if transaction not in self.transactions:
                                self.transactions.append(transaction)
                                if is_arbitrage:
                                    logger.info(f"New arbitrage transaction detected! Profit: {profit} ETH")

            self.last_block = current_block
            return sorted(self.transactions, key=lambda x: x['timestamp'], reverse=True)

        except Exception as e:
            logger.error(f"Error getting blockchain transactions: {e}")
            return []

    def get_contract_balance(self) -> float:
        """Get current contract balance"""
        try:
            balance = self.w3.eth.get_balance(self.contract_address)
            return Web3.from_wei(balance, 'ether')
        except Exception as e:
            logger.error(f"Error getting contract balance: {e}")
            return 0.0

    def get_transaction_count(self) -> int:
        """Get total number of transactions"""
        try:
            return self.w3.eth.get_transaction_count(self.contract_address)
        except Exception as e:
            logger.error(f"Error getting transaction count: {e}")
            return 0

    def get_profit_stats(self) -> Dict[str, float]:
        """Calculate profit statistics from transactions"""
        stats = {
            'total_profit': 0.0,
            'total_cost': 0.0,
            'net_profit': 0.0,
            'avg_gas_price': 0.0
        }

        if not self.transactions:
            return stats

        for tx in self.transactions:
            if tx['success']:
                if tx['is_arbitrage']:
                    stats['total_profit'] += float(tx['profit'])
                stats['total_cost'] += float(tx['cost'])
                stats['avg_gas_price'] += float(tx['gas_price'])

        stats['net_profit'] = stats['total_profit'] - stats['total_cost']
        stats['avg_gas_price'] /= len(self.transactions)

        return stats
