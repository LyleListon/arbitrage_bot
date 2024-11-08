from ledger_wallet import LedgerWallet
from web3 import Web3
from config import NETWORKS, get_rpc_url


def test_ledger_connection():
    print("Testing Ledger connection...")
    print("\nPrerequisites:")
    print("1. Your Ledger is connected via USB")
    print("2. Your Ledger is unlocked")
    print("3. The Ethereum app is open")
    print("4. Contract data is allowed in the Ethereum app settings")
    print("\nTrying to connect...")
    
    try:
        wallet = LedgerWallet()
        print(f"\n✅ Successfully connected to Ledger!")
        print(f"✅ Using address: {wallet.address}")
        
        # Get Sepolia balance
        rpc_url = get_rpc_url('sepolia', NETWORKS['sepolia'])
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        balance = w3.eth.get_balance(wallet.address)
        balance_eth = w3.from_wei(balance, 'ether')
        
        print("\nAccount Details:")
        print(f"Address: {wallet.address}")
        print(f"Sepolia ETH Balance: {balance_eth:.4f} ETH")
        
        # Verify address derivation
        print("\nVerifying address derivation...")
        addr1 = wallet._get_address()
        addr2 = wallet._get_address()
        if addr1 != addr2:
            raise Exception("Address derivation inconsistent!")
        if addr1 != wallet.address:
            raise Exception("Address mismatch!")
            
        print("✅ Address verification successful!")
        print("✅ Device communication working!")
        
        return True
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure your Ledger is properly connected")
        print("2. Unlock your Ledger if it's locked")
        print("3. Open the Ethereum app on your Ledger")
        print("4. In the Ethereum app settings:")
        print("   - Enable 'Contract data' option")
        print("   - Enable 'Debug data' option")
        print("5. Try disconnecting and reconnecting your Ledger")
        print("6. If using Windows, check Device Manager")
        print("   for proper USB connection")
        return False
    finally:
        if 'wallet' in locals():
            wallet.close()


if __name__ == "__main__":
    test_ledger_connection()
