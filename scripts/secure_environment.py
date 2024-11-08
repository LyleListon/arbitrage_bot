"""
Secure environment configuration for mainnet deployment
"""
import os
from eth_account import Account
import secrets
import json


def generate_secure_key():
    """Generate a new secure private key"""
    return secrets.token_hex(32)


def main():
    print("🔒 Securing Mainnet Environment")
    print("=" * 50)
    
    # Check if .env.mainnet exists
    if os.path.exists('.env.mainnet'):
        # Create backup
        with open('.env.mainnet', 'r') as f:
            current_env = f.read()
        with open('.env.mainnet.backup', 'w') as f:
            f.write(current_env)
        print("✓ Created backup of current .env.mainnet")
    
    # Generate new secure private key
    new_private_key = generate_secure_key()
    new_account = Account.from_key(new_private_key)
    
    print("\n⚠️ IMPORTANT: NEW DEPLOYMENT WALLET")
    print("=" * 50)
    print(f"Address: {new_account.address}")
    print(f"Private Key: {new_private_key}")
    print("\n⚠️ SAVE THESE DETAILS SECURELY AND NEVER SHARE THEM")
    print("⚠️ FUND THIS WALLET WITH ONLY THE AMOUNT NEEDED FOR DEPLOYMENT")
    
    # Update .env.mainnet with new wallet but keep other settings
    env_lines = []
    with open('.env.mainnet', 'r') as f:
        for line in f:
            if line.startswith('MAINNET_PRIVATE_KEY='):
                env_lines.append(f'MAINNET_PRIVATE_KEY={new_private_key}\n')
            elif line.startswith('WALLET_ADDRESS='):
                env_lines.append(f'WALLET_ADDRESS={new_account.address}\n')
            else:
                env_lines.append(line)
    
    # Write updated config
    with open('.env.mainnet', 'w') as f:
        f.writelines(env_lines)
    
    print("\n✓ Updated .env.mainnet with secure wallet")
    print("\nNext steps:")
    print("1. Save the wallet details in a secure location")
    print("2. Fund the wallet with deployment amount (approximately 0.5 ETH)")
    print("3. Wait for confirmation of funds")
    print("4. Run scripts/check_mainnet_balance.py to verify funding")
    print("5. Proceed with mainnet deployment")
    
    # Create secure deployment checklist
    checklist = {
        'pre_deployment': [
            'Secure wallet created and funded',
            'Gas prices checked and acceptable',
            'Contract code audited and verified',
            'Test deployment successful on Holesky',
            'Emergency procedures documented',
            'Monitoring systems ready'
        ],
        'deployment': [
            'Deploy PriceFeedIntegration contract',
            'Verify PriceFeedIntegration on Etherscan',
            'Configure Chainlink price feeds',
            'Deploy ArbitrageBot with conservative parameters',
            'Verify ArbitrageBot on Etherscan',
            'Set up token and DEX authorizations'
        ],
        'post_deployment': [
            'Verify all contract parameters',
            'Test emergency shutdown procedure',
            'Monitor initial operations for 24 hours',
            'Set up alerts and notifications',
            'Document all deployed addresses',
            'Secure backup of all deployment info'
        ]
    }
    
    # Save checklist
    with open('DEPLOYMENT_CHECKLIST.json', 'w') as f:
        json.dump(checklist, f, indent=2)
    
    print("\n✓ Created DEPLOYMENT_CHECKLIST.json")


if __name__ == '__main__':
    main()
