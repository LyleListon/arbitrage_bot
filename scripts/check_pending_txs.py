from web3 import Web3
from dotenv import load_dotenv
import os
import time


def main():
    # Load mainnet configuration
    load_dotenv('.env.mainnet')
    w3 = Web3(Web3.HTTPProvider(os.getenv('MAINNET_RPC_URL')))
    print(f"Connected to mainnet: {w3.is_connected()}")
    
    address = '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801'
    
    # Get current block
    current_block = w3.eth.block_number
    print(f"\nCurrent block: {current_block}")
    
    # Check last few blocks for incoming transactions
    print("\nChecking recent blocks for incoming transactions...")
    for block_num in range(current_block - 10, current_block + 1):
        block = w3.eth.get_block(block_num, True)
        block_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block['timestamp']))
        
        for tx in block.transactions:
            if tx['to'] and tx['to'].lower() == address.lower():
                print(f"\nFound incoming transaction in block {block_num}")
                print(f"Time: {block_time}")
                print(f"From: {tx['from']}")
                print(f"Value: {w3.from_wei(tx['value'], 'ether')} ETH")
                print(f"Hash: {tx.hash.hex()}")
    
    # Get current balance
    balance = w3.eth.get_balance(address)
    print(f"\nCurrent balance: {w3.from_wei(balance, 'ether')} ETH")


if __name__ == '__main__':
    main()
