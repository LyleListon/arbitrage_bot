from web3 import Web3
from ledger_wallet import LedgerWallet
import os
from dotenv import load_dotenv

load_dotenv()

def test_ledger_signing():
    print("Testing Ledger transaction signing...")
    print("\nMake sure:")
    print("1. Ledger is connected and unlocked")
    print("2. Ethereum app is open")
    print("3. Blind signing is enabled")
    
    try:
        # Initialize Web3 with Sepolia
        rpc_url = os.getenv('SEPOLIA_RPC_URL')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Connect to Ledger
        wallet = LedgerWallet()
        print(f"\nConnected to address: {wallet.address}")
        
        # Get current nonce and gas price
        nonce = w3.eth.get_transaction_count(wallet.address)
        gas_price = w3.eth.gas_price
        
        # Create a simple transaction (sending 0 ETH to ourselves)
        transaction = {
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 21000,
            'to': wallet.address,
            'value': 0,
            'data': b'',
            'chainId': 11155111  # Sepolia chain ID
        }
        
        print("\nAttempting to sign transaction...")
        print("Transaction details:")
        print(f"From: {wallet.address}")
        print(f"To: {wallet.address}")
        print(f"Value: 0 ETH")
        print(f"Gas Price: {w3.from_wei(gas_price, 'gwei')} Gwei")
        print("\nPlease check your Ledger device...")
        
        # Try to sign the transaction
        signed_txn = wallet.sign_transaction(transaction)
        
        print("\n✅ Transaction signed successfully!")
        print("Your Ledger is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure Ethereum app is open")
        print("2. Check that Blind signing is enabled")
        print("3. Try reconnecting your Ledger")
        return False
    finally:
        if 'wallet' in locals():
            wallet.close()

if __name__ == "__main__":
    test_ledger_signing()
