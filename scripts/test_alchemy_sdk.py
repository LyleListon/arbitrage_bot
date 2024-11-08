from alchemy import Alchemy, Network
import os
from dotenv import load_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3

def test_alchemy_transaction():
    load_dotenv()
    
    # Configure Alchemy
    settings = {
        "api_key": os.getenv('ALCHEMY_API_KEY'),
        "network": Network.ETH_HOLESKY
    }
    
    alchemy = Alchemy(settings)
    w3 = Web3(Web3.HTTPProvider(f"https://eth-holesky.g.alchemy.com/v2/{settings['api_key']}"))
    
    print("Testing connection...")
    print(f"Connected: {w3.is_connected()}")
    print(f"Chain ID: {w3.eth.chain_id}")
    
    # Get account from private key
    account: LocalAccount = Account.from_key(os.getenv('PRIVATE_KEY'))
    print(f"\nAccount address: {account.address}")
    
    balance = w3.eth.get_balance(account.address)
    print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")
    
    try:
        # Get the latest block number using Alchemy SDK
        latest_block = alchemy.core.get_block_number()
        print(f"\nLatest block number: {latest_block}")
        
        # Build a simple transaction
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.eth.gas_price
        
        transaction = {
            'nonce': nonce,
            'to': account.address,
            'value': 0,
            'gas': 21000,
            'gasPrice': gas_price,
            'chainId': w3.eth.chain_id
        }
        
        print("\nSigning transaction...")
        signed = account.sign_transaction(transaction)
        
        print("Sending raw transaction...")
        tx_hash = alchemy.core.send_raw_transaction(signed.rawTransaction)
        print(f"Transaction hash: {tx_hash.hex()}")
        
        print("Waiting for receipt...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction successful! Block number: {receipt['blockNumber']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_alchemy_transaction()
