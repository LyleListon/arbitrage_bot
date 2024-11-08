from web3 import Web3
import time
import os
import argparse
from dotenv import load_dotenv
from database import save_trade
from config import (
    MIN_PROFIT_PERCENTAGE,
    TRADE_AMOUNT,
    SLIPPAGE_TOLERANCE,
    NETWORKS,
    get_config_token_pairs,
    get_network_config,
    get_rpc_url
)
from ledger_wallet import LedgerWallet

load_dotenv()


class ArbitrageBotLedger:
    def __init__(self, network: str):
        self.network = network
        self.config = NETWORKS.get(network, NETWORKS['ethereum'])
        
        # Get network-specific RPC URL
        rpc_url = get_rpc_url(network, self.config)
        if not rpc_url:
            raise ValueError(f"RPC URL not found for network {network}")
        
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Initialize Ledger wallet
        print("Connect Ledger and open Ethereum app...")
        self.wallet = LedgerWallet()
        print(f"Using address: {self.wallet.address}")
        
        # Load contracts
        self.load_contracts()

    def load_contracts(self):
        """Load smart contracts for arbitrage and price feed."""
        contract_address = os.getenv(
            f'{self.network.upper()}_CONTRACT_ADDRESS'
        )
        if not contract_address:
            raise ValueError(
                f"Contract address not found for network {self.network}"
            )
        
        # Load contract ABIs
        with open('contracts/ArbitrageBot.json', 'r') as f:
            arbitrage_abi = f.read()
        
        with open('contracts/PriceFeedIntegration.json', 'r') as f:
            price_feed_abi = f.read()
        
        # Initialize contract instances
        self.arbitrage_contract = self.w3.eth.contract(
            address=contract_address,
            abi=arbitrage_abi
        )
        
        price_feed_addr = os.getenv(
            f'{self.network.upper()}_PRICE_FEED_ADDRESS'
        )
        self.price_feed = self.w3.eth.contract(
            address=price_feed_addr,
            abi=price_feed_abi
        )

    def check_arbitrage_opportunity(self, token_pair):
        """Check for arbitrage opportunities between token pairs."""
        try:
            prices = self.price_feed.functions.getLatestPrices(
                token_pair['tokenA'],
                token_pair['tokenB']
            ).call()
            
            price_a, price_b = prices
            profit_percentage = (price_a / price_b - 1) * 100
            
            return (
                profit_percentage > MIN_PROFIT_PERCENTAGE,
                price_a,
                price_b,
                profit_percentage
            )
        except Exception as e:
            print(f"Error checking prices: {str(e)}")
            return False, 0, 0, 0

    def execute_trade(self, amount_in, amount_out_min, path):
        """Execute trade using Ledger wallet for signing."""
        try:
            # Get current nonce
            nonce = self.w3.eth.get_transaction_count(self.wallet.address)
            
            # Prepare transaction
            transaction = self.arbitrage_contract.functions.executeTrade(
                amount_in,
                amount_out_min,
                path
            ).build_transaction({
                'from': self.wallet.address,
                'gas': 250000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign transaction with Ledger
            print("Please review and confirm the transaction on Ledger...")
            signed_txn = self.wallet.sign_transaction(transaction)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn)
            
            # Wait for transaction receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Save trade details
            timestamp = int(time.time())
            save_trade(self.network, amount_in, amount_out_min, timestamp)
            
            return tx_receipt
            
        except Exception as e:
            print(f"Error executing trade: {str(e)}")
            return None

    def run(self):
        """Main arbitrage bot loop."""
        network_config = get_network_config(self.network)
        min_profit = network_config['min_profit_percentage']
        check_interval = network_config['check_interval']
        
        print(f"Starting arbitrage bot on {self.network}...")
        print(f"Monitoring prices with min profit: {min_profit}%")
        
        while True:
            for token_pair in get_config_token_pairs(self.network):
                opportunity, price_a, price_b, profit = (
                    self.check_arbitrage_opportunity(token_pair)
                )
                
                if opportunity:
                    print(
                        f"\nArbitrage opportunity found for "
                        f"{token_pair['symbol']}"
                    )
                    print(f"Potential profit: {profit:.2f}%")
                    
                    # Calculate minimum output with slippage tolerance
                    amount_out_min = int(
                        TRADE_AMOUNT * (1 + profit / 100) * SLIPPAGE_TOLERANCE
                    )
                    
                    # Prepare token path
                    path = [
                        os.getenv(token_pair['tokenA']),
                        os.getenv(token_pair['tokenB'])
                    ]
                    
                    # Execute trade
                    tx_receipt = self.execute_trade(
                        TRADE_AMOUNT,
                        amount_out_min,
                        path
                    )
                    
                    if tx_receipt:
                        print(
                            "Trade executed successfully! "
                            f"Hash: {tx_receipt.transactionHash.hex()}"
                        )
                    else:
                        print("Trade execution failed")
                else:
                    print(
                        f"\rChecking {token_pair['symbol']} - "
                        f"Current spread: {profit:.2f}%",
                        end=""
                    )
            
            time.sleep(check_interval)

    def close(self):
        """Clean up resources."""
        if hasattr(self, 'wallet'):
            self.wallet.close()


def main():
    parser = argparse.ArgumentParser(
        description="Run arbitrage bot with Ledger"
    )
    parser.add_argument(
        '--network',
        choices=list(NETWORKS.keys()),
        default='sepolia',
        help="Network to run on"
    )
    
    args = parser.parse_args()
    
    bot = ArbitrageBotLedger(args.network)
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nShutting down bot...")
    finally:
        bot.close()


if __name__ == "__main__":
    main()
