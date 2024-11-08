from web3 import Web3
import os
from dotenv import load_dotenv

def test_transaction():
    load_dotenv()
    
    # Get RPC URL and private key
    rpc_url = os.getenv('HOLESKY_RPC_URL')
    private_key = os.getenv('PRIVATE_KEY')
    
    print(f"Using RPC URL: {rpc_url}")
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Failed to connect to network")
        return
        
    print("✅ Connected to network")
    print(f"Chain ID: {w3.eth.chain_id}")
    
    # Get account from private key
    account = w3.eth.account.from_key(private_key)
    print(f"Account address: {account.address}")
    
    balance = w3.eth.get_balance(account.address)
    print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")
    
    # Build a simple transaction
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        gas_price = w3.eth.gas_price
        
        # Create a transaction sending 0 ETH to ourselves
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
        
        print("Sending transaction...")
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"Transaction hash: {tx_hash.hex()}")
        
        print("Waiting for receipt...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction successful! Block number: {receipt['blockNumber']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_transaction()
