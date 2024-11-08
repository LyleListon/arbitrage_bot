"""
Security check before mainnet deployment
"""
import os
import json
from datetime import datetime


def check_environment():
    """Check environment configuration"""
    issues = []
    
    # Check .env.mainnet
    if not os.path.exists('.env.mainnet'):
        issues.append("❌ .env.mainnet file not found")
    else:
        with open('.env.mainnet', 'r') as f:
            env_content = f.read()
            
            # Check for exposed private key
            if 'MAINNET_PRIVATE_KEY=' in env_content:
                issues.append("⚠️ WARNING: Private key found in .env.mainnet")
            
            # Check required variables
            required_vars = [
                'MAINNET_RPC_URL',
                'WALLET_ADDRESS',
                'MAX_TRADE_SIZE',
                'MIN_PROFIT_THRESHOLD',
                'MAX_SLIPPAGE',
                'MAX_GAS_PRICE_GWEI'
            ]
            
            for var in required_vars:
                if var not in env_content:
                    issues.append(f"❌ Missing required variable: {var}")
    
    # Create security checklist
    checklist = {
        'timestamp': datetime.now().isoformat(),
        'security_checks': [
            {
                'name': 'Environment Configuration',
                'status': 'FAIL' if issues else 'PASS',
                'issues': issues
            }
        ],
        'deployment_requirements': {
            'contracts': [
                'PriceFeedIntegration',
                'ArbitrageBot'
            ],
            'price_feeds': {
                'ETH/USD': '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',
                'USDC/USD': '0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6'
            },
            'tokens': {
                'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
            },
            'dexs': {
                'Uniswap V2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
            }
        },
        'recommendations': [
            'Create new deployment wallet',
            'Fund wallet with exact deployment amount',
            'Store private key securely',
            'Enable all safety features',
            'Start with minimum trade sizes',
            'Monitor continuously after deployment'
        ]
    }
    
    # Save checklist
    with open('SECURITY_CHECKLIST.json', 'w') as f:
        json.dump(checklist, f, indent=2)
    
    # Print results
    print("\n🔒 Security Check Results")
    print("=" * 50)
    
    if issues:
        print("\nIssues Found:")
        for issue in issues:
            print(issue)
        print("\n⚠️ Please resolve these issues before proceeding with mainnet deployment")
    else:
        print("\n✓ No immediate security issues found")
    
    print("\nRecommendations:")
    for rec in checklist['recommendations']:
        print(f"• {rec}")
    
    print("\n✓ Created SECURITY_CHECKLIST.json")
    print("\nNext steps:")
    print("1. Review SECURITY_CHECKLIST.json")
    print("2. Create new deployment wallet")
    print("3. Update .env.mainnet with new wallet")
    print("4. Fund wallet with deployment amount")
    print("5. Run final verification before deployment")


if __name__ == '__main__':
    check_environment()
