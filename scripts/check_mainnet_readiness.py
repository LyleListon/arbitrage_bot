"""
Check mainnet readiness and deployment requirements
"""
import os
from dotenv import load_dotenv
import json


def check_environment():
    """Check environment variables and configuration"""
    load_dotenv('.env.mainnet')
    
    required_vars = {
        'Network': [
            'MAINNET_RPC_URL',
            'MAINNET_WSS_URL'
        ],
        'Contracts': [
            'WETH_ADDRESS',
            'USDC_ADDRESS',
            'UNISWAP_V2_ROUTER'
        ],
        'Price Feeds': [
            'ETH_USD_PRICE_FEED',
            'USDC_USD_PRICE_FEED'
        ],
        'Configuration': [
            'MAX_TRADE_SIZE',
            'MIN_PROFIT_THRESHOLD',
            'MAX_SLIPPAGE',
            'MAX_GAS_PRICE_GWEI'
        ],
        'Safety': [
            'POSITION_SIZING_ENABLED',
            'DYNAMIC_GAS_PRICING',
            'MEV_PROTECTION_ENABLED',
            'SLIPPAGE_PROTECTION_ENABLED'
        ]
    }
    
    results = {}
    for category, vars in required_vars.items():
        results[category] = {}
        for var in vars:
            value = os.getenv(var)
            results[category][var] = {
                'present': value is not None,
                'value': value if value else 'Not set'
            }
    
    return results


def check_contract_files():
    """Check required contract files"""
    required_files = {
        'Contracts': [
            'contracts/ArbitrageBot.sol',
            'contracts/PriceFeedIntegration.sol'
        ],
        'ABIs': [
            'abi/ArbitrageBot.json',
            'abi/PriceFeedIntegration.json'
        ],
        'Scripts': [
            'scripts/deploy_mainnet.py',
            'scripts/verify_deployment.py',
            'dashboard/app.py'
        ]
    }
    
    results = {}
    for category, files in required_files.items():
        results[category] = {}
        for file in files:
            results[category][file] = os.path.exists(file)
    
    return results


def main():
    print("\n🔍 Checking Mainnet Deployment Readiness")
    print("=" * 50)
    
    # Check environment
    print("\nEnvironment Variables:")
    print("-" * 50)
    env_results = check_environment()
    
    for category, vars in env_results.items():
        print(f"\n{category}:")
        for var, status in vars.items():
            print(f"{'✓' if status['present'] else '✗'} {var}")
            if not status['present']:
                print(f"  Missing: {var}")
    
    # Check files
    print("\nRequired Files:")
    print("-" * 50)
    file_results = check_contract_files()
    
    for category, files in file_results.items():
        print(f"\n{category}:")
        for file, exists in files.items():
            print(f"{'✓' if exists else '✗'} {file}")
    
    # Save results
    results = {
        'timestamp': 'pre-deployment',
        'environment': env_results,
        'files': file_results,
        'recommendations': [
            'Review all configuration values',
            'Ensure price feeds are correct',
            'Verify contract addresses',
            'Check gas prices before deployment',
            'Have monitoring ready',
            'Test emergency procedures'
        ]
    }
    
    with open('mainnet_readiness.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\nReadiness Report:")
    print("-" * 50)
    env_ready = all(all(v['present'] for v in vars.values()) 
                   for vars in env_results.values())
    files_ready = all(all(exists for exists in files.values()) 
                     for files in file_results.values())
    
    if env_ready and files_ready:
        print("✓ System ready for mainnet deployment")
        print("\nNext steps:")
        print("1. Review mainnet_readiness.json")
        print("2. Check current gas prices")
        print("3. Verify Chainlink price feeds")
        print("4. Deploy contracts")
        print("5. Set up monitoring")
    else:
        print("✗ System not ready for deployment")
        print("Please fix the issues marked with ✗ above")


if __name__ == '__main__':
    main()
