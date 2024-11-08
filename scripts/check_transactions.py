from web3 import Web3
import time
from eth_typing import HexStr


def main():
    # Initialize web3 with Alchemy
    w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.g.alchemy.com/v2/kRXhWVt8YU_8LnGS20145F5uBDFbL_k0'))
    address = '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801'
    
    # Get current block and balance
    current_block = w3.eth.block_number
    balance = w3.eth.get_balance(address)
    print(f"Current block: {current_block}")
    print(f"Current balance: {w3.from_wei(balance, 'ether')} ETH")
    
    # Check pending transactions
    print("\nChecking pending transactions...")
    pending_block = w3.eth.get_block('pending', True)
    for tx in pending_block.transactions:
        if tx['to'] and tx['to'].lower() == address.lower():
            print(f"\nPending incoming transaction:")
            print(f"  From: {tx['from']}")
            print(f"  Value: {w3.from_wei(tx['value'], 'ether')} ETH")
            print(f"  Hash: {tx.hash.hex()}")
    
    # Check last 100 blocks
    print("\nChecking last 100 blocks for transactions...")
    for block_num in range(current_block - 100, current_block + 1):
        try:
            block = w3.eth.get_block(block_num, True)
            
            # Check if block has any transactions to/from our address
            block_has_tx = False
            for tx in block.transactions:
                if ((tx['to'] and tx['to'].lower() == address.lower()) or 
                    tx['from'].lower() == address.lower()):
                    if not block_has_tx:
                        print(f"\nBlock {block_num} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block.timestamp))}):")
                        block_has_tx = True
                    
                    if tx['to'] and tx['to'].lower() == address.lower():
                        print(f"Incoming transaction:")
                        print(f"  From: {tx['from']}")
                        print(f"  Value: {w3.from_wei(tx['value'], 'ether')} ETH")
                        print(f"  Hash: {tx.hash.hex()}")
                        print(f"  Gas Price: {w3.from_wei(tx['gasPrice'], 'gwei')} gwei")
                    elif tx['from'].lower() == address.lower():
                        print(f"Outgoing transaction:")
                        print(f"  To: {tx['to']}")
                        print(f"  Value: {w3.from_wei(tx['value'], 'ether')} ETH")
                        print(f"  Hash: {tx.hash.hex()}")
                        print(f"  Gas Price: {w3.from_wei(tx['gasPrice'], 'gwei')} gwei")
        except Exception as e:
            print(f"Error getting block {block_num}: {str(e)}")
            continue


if __name__ == '__main__':
    main()
