#!/usr/bin/env python3

from web3 import Web3
import os
from dotenv import load_dotenv
import sys


def test_alchemy_connection():
    """Test connection to Alchemy Holesky endpoint."""
    # Load environment variables
    load_dotenv()
    
    # Get the RPC URL
    rpc_url = os.getenv('HOLESKY_RPC_URL')
    if not rpc_url:
        print("❌ Error: HOLESKY_RPC_URL not found in .env file")
        sys.exit(1)
    
    try:
        # Initialize Web3
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Test connection
        is_connected = w3.is_connected()
        if not is_connected:
            print("❌ Error: Could not connect to Alchemy endpoint")
            sys.exit(1)
        
        # Get chain info
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        
        print("\nAlchemy Holesky Connection Test:")
        print(f"✅ Connected: {is_connected}")
        print(f"✅ Chain ID: {chain_id}")
        print(f"✅ Latest Block: {block_number}")
        
        # Test account access
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            print("❌ Error: PRIVATE_KEY not found in .env file")
            sys.exit(1)
            
        account = w3.eth.account.from_key(private_key)
        balance = w3.eth.get_balance(account.address)
        
        print(f"\nAccount Details:")
        print(f"✅ Address: {account.address}")
        print(f"✅ Balance: {w3.from_wei(balance, 'ether')} ETH")
        
        # Test transaction building
        print("\nTesting transaction building...")
        try:
            # Build a test transaction
            nonce = w3.eth.get_transaction_count(account.address)
            transaction = {
                'chainId': chain_id,
                'nonce': nonce,
                'to': account.address,
                'value': 0,
                'gas': 21000,
                'gasPrice': w3.eth.gas_price
            }
            
            # Sign the transaction (but don't send it)
            signed = account.sign_transaction(transaction)
            print("✅ Successfully built and signed transaction")
            print(f"✅ Transaction hash would be: {w3.to_hex(w3.keccak(signed.rawTransaction))}")
            
            # Test sending raw transaction
            print("\nTesting eth_sendRawTransaction...")
            try:
                tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                print(f"✅ Transaction sent! Hash: {tx_hash.hex()}")
            except Exception as e:
                print(f"❌ Error sending transaction: {str(e)}")
            
        except Exception as e:
            print(f"❌ Error building transaction: {str(e)}")
        
    except Exception as e:
        print(f"\n❌ Connection Error: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    print("Testing Alchemy Holesky connection...")
    test_alchemy_connection()
