"""
Prepare for mainnet deployment by checking environment and estimating costs
"""
from web3 import Web3
from dotenv import load_dotenv
import json
import os


def load_contract_abi(name):
    """Load contract ABI from file"""
    with open(f'abi/{name}.json', 'r') as f:
        return json.load(f)


def check_chainlink_feeds(w3):
    """Verify Chainlink price feeds are working"""
    feeds = {
        'ETH/USD': '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',
        'USDC/USD': '0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6'
    }
    
    aggregator_abi = [
        {
            "inputs": [],
            "name": "latestRoundData",
            "outputs": [
                {"internalType": "uint80", "name": "roundId", "type": "uint80"},
                {"internalType": "int256", "name": "answer", "type": "int256"},
                {"internalType": "uint256", "name": "startedAt", "type": "uint256"},
                {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
                {"internalType": "uint80", "name": "answeredInRound", "type": "uint80"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    results = {}
    for name, address in feeds.items():
        try:
            feed = w3.eth.contract(address=address, abi=aggregator_abi)
            _, price, _, timestamp, _ = feed.functions.latestRoundData().call()
            results[name] = {
                'working': True,
                'price': price / 1e8,
                'timestamp': timestamp
            }
        except Exception as e:
            results[name] = {
                'working': False,
                'error': str(e)
            }
    
    return results


def estimate_deployment_costs(w3):
    """Estimate deployment and setup costs"""
    gas_price = w3.eth.gas_price
    
    # Estimated gas usage from testnet
    estimates = {
        'PriceFeedIntegration': {
            'deployment': 1000000,
            'setup': 200000
        },
        'ArbitrageBot': {
            'deployment': 2000000,
            'setup': 300000
        }
    }
    
    total_gas = sum(sum(contract.values()) for contract in estimates.values())
    total_cost = w3.from_wei(total_gas * gas_price, 'ether')
    
    return {
        'gas_price_gwei': w3.from_wei(gas_price, 'gwei'),
        'total_gas': total_gas,
        'total_cost_eth': total_cost,
        'details': estimates
    }


def main():
    print("\n🚀 Preparing for Mainnet Deployment")
    print("=" * 50)
    
    # Load mainnet configuration
    load_dotenv('.env.mainnet')
    rpc_url = os.getenv('MAINNET_RPC_URL')
    if not rpc_url:
        raise ValueError("MAINNET_RPC_URL not found in environment")
    
    # Connect to mainnet
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise Exception("Failed to connect to mainnet")
    
    print(f"Connected to mainnet (Chain ID: {w3.eth.chain_id})")
    
    # Check Chainlink feeds
    print("\nVerifying Chainlink Price Feeds:")
    print("-" * 50)
    feeds = check_chainlink_feeds(w3)
    for name, result in feeds.items():
        if result['working']:
            print(f"{name}: ✓ Working")
            print(f"  Price: ${result['price']:.2f}")
            print(f"  Last Update: {result['timestamp']}")
        else:
            print(f"{name}: ✗ Error - {result['error']}")
    
    # Estimate costs
    print("\nEstimating Deployment Costs:")
    print("-" * 50)
    costs = estimate_deployment_costs(w3)
    print(f"Current Gas Price: {costs['gas_price_gwei']:.2f} Gwei")
    print(f"Total Gas Required: {costs['total_gas']:,}")
    print(f"Estimated Total Cost: {costs['total_cost_eth']:.4f} ETH")
    
    # Check contract addresses
    print("\nVerifying Contract Addresses:")
    print("-" * 50)
    contracts = {
        'WETH': os.getenv('WETH_ADDRESS'),
        'USDC': os.getenv('USDC_ADDRESS'),
        'Uniswap V2 Router': os.getenv('UNISWAP_V2_ROUTER')
    }
    
    for name, address in contracts.items():
        if not address:
            print(f"{name}: ✗ Address not found in environment")
            continue
        
        code = w3.eth.get_code(address)
        print(f"{name}: {'✓' if len(code) > 2 else '✗'} {address}")
    
    # Verify configuration
    print("\nVerifying Configuration:")
    print("-" * 50)
    required_vars = [
        'MAX_TRADE_SIZE',
        'MIN_PROFIT_THRESHOLD',
        'MAX_SLIPPAGE',
        'MAX_GAS_PRICE_GWEI'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        print(f"{var}: {'✓' if value else '✗'} {value if value else 'Not set'}")
    
    print("\nNext Steps:")
    print("1. Review Chainlink feed status")
    print("2. Evaluate gas costs and timing")
    print("3. Verify all contract addresses")
    print("4. Double-check configuration values")
    print("5. Ensure monitoring is ready")
    print("6. Prepare emergency procedures")
    print("7. Schedule deployment window")


if __name__ == '__main__':
    main()
