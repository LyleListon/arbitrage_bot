from web3 import Web3
from dotenv import load_dotenv
import json
import os


def load_contract(w3, name, address):
    """Load contract ABI and create contract instance"""
    with open(f'abi/{name}.json', 'r') as f:
        abi = json.load(f)
    return w3.eth.contract(address=address, abi=abi)


def main():
    # Load environment and connect to Holesky
    load_dotenv('.env.holesky')
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    print(f"Connected to Holesky: {w3.is_connected()}")
    
    # Load mock feed contract
    mock_feed = load_contract(w3, 'MockPriceFeed', os.getenv('HOLESKY_PRICE_FEED_ADDRESS'))
    
    # Token addresses
    tokens = {
        'WETH': os.getenv('WETH_ADDRESS'),
        'USDC': os.getenv('USDC_ADDRESS')
    }
    
    # Check each token's price feed
    print("\nPrice Feed Status:")
    print("-" * 50)
    
    for name, token in tokens.items():
        print(f"\n{name} ({token}):")
        
        try:
            # Get price feed info
            price, decimals, is_active = mock_feed.functions.getPriceFeedInfo(token).call()
            print(f"Active: {'✓' if is_active else '✗'}")
            print(f"Decimals: {decimals}")
            print(f"Raw Price: {price}")
            
            # Get latest price
            if is_active:
                latest_price, timestamp = mock_feed.functions.getLatestPrice(token).call()
                print(f"Latest Price: ${latest_price / 10**decimals:.2f}")
                print(f"Last Updated: {timestamp}")
            
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == '__main__':
    main()
