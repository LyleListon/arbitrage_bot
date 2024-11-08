from eth_account import Account
import secrets
import json

def generate_wallet():
    # Generate a random private key
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)
    
    wallet_info = {
        "address": account.address,
        "private_key": private_key,
    }
    
    # Save to file
    with open('holesky_wallet.json', 'w') as f:
        json.dump(wallet_info, f, indent=4)
        
    print("\nNew wallet generated for Holesky testnet:")
    print(f"Address: {account.address}")
    print(f"Private key: {private_key}")
    print("\nWallet info saved to holesky_wallet.json")
    print("\nIMPORTANT: Keep your private key secure and never share it!")
    print("Get test ETH from: https://holesky-faucet.pk910.de/")

if __name__ == "__main__":
    generate_wallet()
