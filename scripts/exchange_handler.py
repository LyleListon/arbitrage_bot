from web3 import Web3
from .key_manager import KeyManager

class ExchangeHandler:
    def __init__(self, config, key_manager: KeyManager, w3: Web3):
        self.config = config
        self.key_manager = key_manager
        self.w3 = w3

    def get_token_price(self, network: str, token_address: str) -> float:
        # Implement token price fetching logic here
        # For now, we'll return a mock price
        return 1.0

    def execute_swap(self, network: str, token_in: str, token_out: str, amount_in: int, min_amount_out: int, from_address: str):
        try:
            # Get the private key
            private_key = self.key_manager.get_key('BINANCE_SMART_CHAIN_PRIVATE_KEY')
            print(f"Debug: Private key (first 6 chars): {private_key[:6]}...")

            # Create a mock transaction for demonstration
            transaction = {
                'to': Web3.to_checksum_address(token_out),
                'value': amount_in,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(from_address),
                'chainId': 97,  # BSC Testnet chain ID
            }

            # Sign the transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            print(f"Debug: Signed transaction hash: {signed_txn.hash.hex()}")

            # Send the transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Debug: Transaction hash: {tx_hash.hex()}")

            # Wait for the transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Debug: Transaction receipt status: {tx_receipt['status']}")

            return {'status': 'success', 'tx_hash': tx_hash.hex()}
        except Exception as e:
            print(f"Error in execute_swap:")
            print(f"  Network: {network}")
            print(f"  Token In: {token_in}")
            print(f"  Token Out: {token_out}")
            print(f"  Error: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
