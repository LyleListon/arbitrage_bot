from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

def test_alchemy_connection():
    # Get RPC URL from environment
    rpc_url = os.getenv('HOLESKY_RPC_URL')
    print(f"Using RPC URL: {rpc_url}")
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Test basic connection
    connected = w3.is_connected()
    print(f"Connected to network: {connected}")
    
    if connected:
        # Get network info
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        gas_price = w3.eth.gas_price
        
        print(f"Chain ID: {chain_id}")
        print(f"Latest block number: {block_number}")
        print(f"Current gas price: {w3.from_wei(gas_price, 'gwei')} Gwei")
        
        # Get account info
        private_key = os.getenv('PRIVATE_KEY')
        account = w3.eth.account.from_key(private_key)
        balance = w3.eth.get_balance(account.address)
        
        print(f"\nAccount address: {account.address}")
        print(f"Account balance: {w3.from_wei(balance, 'ether')} ETH")
        
        # Test transaction building
        print("\nTesting transaction building...")
        try:
            # Build a simple transaction
            transaction = {
                'chainId': chain_id,
                'nonce': w3.eth.get_transaction_count(account.address),
                'to': account.address,
                'value': 0,
                'gas': 21000,
                'gasPrice': gas_price
            }
            
            # Sign the transaction
            signed = account.sign_transaction(transaction)
            print("✅ Successfully built and signed transaction")
            
            # Don't actually send it
            print("Transaction hash would be:", w3.to_hex(w3.keccak(signed.rawTransaction)))
            
        except Exception as e:
            print(f"❌ Error building transaction: {str(e)}")
    
    else:
        print("Failed to connect to network")

if __name__ == "__main__":
    test_alchemy_connection()
