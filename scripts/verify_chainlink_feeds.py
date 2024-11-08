from web3 import Web3
from dotenv import load_dotenv
import json
import os


def load_abi(name):
    """Load ABI from file"""
    with open(f'abi/{name}.json', 'r') as f:
        return json.load(f)


def main():
    # Load Holesky configuration
    load_dotenv('.env.holesky')
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    print(f"Connected to Holesky: {w3.is_connected()}")
    
    # Chainlink feed addresses
    feeds = {
        'ETH/USD': '0x694AA1769357215DE4FAC081bf1f309aDC325306',
        'USDC/USD': '0x572dDec9087154dC5dfBB1546Bb62713147e0Ab0'
    }
    
    # Load Chainlink aggregator ABI
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
        },
        {
            "inputs": [],
            "name": "decimals",
            "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    print("\nVerifying Chainlink Price Feeds:")
    print("-" * 50)
    
    for name, address in feeds.items():
        print(f"\nChecking {name} feed:")
        print(f"Address: {address}")
        
        try:
            # Create contract instance
            feed = w3.eth.contract(address=address, abi=aggregator_abi)
            
            # Get decimals
            decimals = feed.functions.decimals().call()
            print(f"Decimals: {decimals}")
            
            # Get latest price
            roundId, answer, startedAt, updatedAt, answeredInRound = feed.functions.latestRoundData().call()
            price = answer / 10 ** decimals
            
            print(f"Latest Price: ${price:.2f}")
            print(f"Last Updated: {updatedAt}")
            print(f"Round ID: {roundId}")
            print("✓ Feed is working")
            
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    # Also check our tokens
    tokens = {
        'WETH': os.getenv('WETH_ADDRESS'),
        'USDC': os.getenv('USDC_ADDRESS')
    }
    
    print("\nVerifying Token Addresses:")
    print("-" * 50)
    
    for name, address in tokens.items():
        print(f"\n{name}:")
        print(f"Address: {address}")
        try:
            code = w3.eth.get_code(address)
            print(f"Contract exists: {'✓' if len(code) > 2 else '✗'}")
        except Exception as e:
            print(f"✗ Error: {str(e)}")


if __name__ == '__main__':
    main()
