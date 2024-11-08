from web3 import Web3
from dotenv import load_dotenv
import os


def main():
    # Try multiple RPC providers
    rpcs = [
        'https://eth-mainnet.g.alchemy.com/v2/kRXhWVt8YU_8LnGS20145F5uBDFbL_k0',
        'https://mainnet.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161',  # Public Infura
        'https://rpc.ankr.com/eth',  # Public Ankr
        'https://cloudflare-eth.com'  # Cloudflare
    ]
    
    address = '0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801'
    
    for rpc in rpcs:
        try:
            print(f"\nTrying RPC: {rpc}")
            w3 = Web3(Web3.HTTPProvider(rpc))
            if w3.is_connected():
                balance = w3.eth.get_balance(address)
                print(f'Balance: {w3.from_wei(balance, "ether")} ETH')
                print(f'Block Number: {w3.eth.block_number}')
            else:
                print("Failed to connect")
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == '__main__':
    main()
