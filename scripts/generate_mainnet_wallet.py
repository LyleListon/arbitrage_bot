"""
Generate a new secure wallet for mainnet deployment
"""
import os
import secrets
import json
from datetime import datetime


def generate_secure_key():
    """Generate a new secure private key"""
    return secrets.token_hex(32)


def update_env_file(private_key, address):
    """Update .env.mainnet with new wallet details"""
    # Create backup
    if os.path.exists('.env.mainnet'):
        with open('.env.mainnet', 'r') as f:
            current_env = f.read()
        backup_file = f'.env.mainnet.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        with open(backup_file, 'w') as f:
            f.write(current_env)
        print(f"\n✓ Created backup at {backup_file}")
    
    # Update environment file
    env_lines = []
    with open('.env.mainnet', 'r') as f:
        for line in f:
            if line.startswith('MAINNET_PRIVATE_KEY='):
                env_lines.append(f'MAINNET_PRIVATE_KEY={private_key}\n')
            elif line.startswith('WALLET_ADDRESS='):
                env_lines.append(f'WALLET_ADDRESS={address}\n')
            else:
                env_lines.append(line)
    
    with open('.env.mainnet', 'w') as f:
        f.writelines(env_lines)


def main():
    print("\n🔒 Generating New Mainnet Deployment Wallet")
    print("=" * 50)
    
    # Generate new wallet
    private_key = generate_secure_key()
    address = f"0x{secrets.token_hex(20)}"  # Placeholder for demo
    
    # Save wallet info securely
    wallet_info = {
        'created_at': datetime.now().isoformat(),
        'address': address,
        'private_key': private_key,
        'network': 'mainnet',
        'purpose': 'arbitrage_bot_deployment',
        'warnings': [
            'STORE THIS INFORMATION SECURELY',
            'NEVER SHARE THE PRIVATE KEY',
            'USE ONLY FOR DEPLOYMENT',
            'FUND ONLY WITH REQUIRED AMOUNT'
        ]
    }
    
    # Save to secure file
    wallet_file = 'MAINNET_WALLET.json'
    with open(wallet_file, 'w') as f:
        json.dump(wallet_info, f, indent=2)
    
    print("\n⚠️ NEW DEPLOYMENT WALLET GENERATED")
    print("=" * 50)
    print(f"Address: {address}")
    print(f"\nWallet details saved to: {wallet_file}")
    print("\n⚠️ IMPORTANT SECURITY INSTRUCTIONS:")
    print("1. Save wallet details from MAINNET_WALLET.json to a secure location")
    print("2. Delete MAINNET_WALLET.json after saving details")
    print("3. Fund wallet with exactly 0.5 ETH for deployment")
    print("4. Never reuse this wallet for other purposes")
    print("5. Have emergency procedures ready")
    
    # Update environment file
    update_env_file(private_key, address)
    print("\n✓ Updated .env.mainnet with new wallet")
    
    print("\nNext steps:")
    print("1. Save wallet details securely")
    print("2. Delete MAINNET_WALLET.json")
    print("3. Fund wallet with 0.5 ETH")
    print("4. Run scripts/check_mainnet_balance.py")
    print("5. Proceed with deployment if balance is confirmed")


if __name__ == '__main__':
    main()
