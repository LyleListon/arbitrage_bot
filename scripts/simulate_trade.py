"""
Script to simulate a trade for testing
"""
import os
import sys
import time
from web3 import Web3
from dotenv import load_dotenv

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from scripts.database import save_trade


def main():
    """Simulate a trade and save to database"""
    # Load environment variables
    load_dotenv('.env.holesky')
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    if not w3.is_connected():
        raise Exception("Failed to connect to network")
    
    print(f"Connected to network. Chain ID: {w3.eth.chain_id}")
    
    # Simulate a successful trade
    trade_data = {
        'network': 'holesky',
        'timestamp': int(time.time()),
        'token_in': os.getenv('WETH_ADDRESS'),
        'token_out': os.getenv('USDC_ADDRESS'),
        'amount_in': w3.to_wei(0.1, 'ether'),  # 0.1 ETH
        'amount_out': int(195 * 1e6),  # 195 USDC (after fees)
        'profit': w3.to_wei(0.002, 'ether'),  # 0.002 ETH profit
        'gas_used': 150000,
        'gas_price': w3.to_wei(1, 'gwei'),
        'success': True,
        'tx_hash': '0x' + 'f' * 64  # Dummy transaction hash
    }
    
    # Save to database
    save_trade(trade_data)
    print("✅ Test trade saved to database")
    print("\nTrade details:")
    print(f"Amount in: {w3.from_wei(trade_data['amount_in'], 'ether')} ETH")
    print(f"Amount out: {trade_data['amount_out'] / 1e6} USDC")
    print(f"Profit: {w3.from_wei(trade_data['profit'], 'ether')} ETH")


if __name__ == "__main__":
    main()
