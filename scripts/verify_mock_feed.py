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
    
    # Load account and contract
    account = w3.eth.account.from_key(os.getenv('HOLESKY_PRIVATE_KEY'))
    mock_feed = load_contract(w3, 'MockPriceFeed', os.getenv('HOLESKY_PRICE_FEED_ADDRESS'))
    
    print("\nContract Info:")
    print(f"Address: {mock_feed.address}")
    print(f"Our Address: {account.address}")
    
    # Check ownership
    owner = mock_feed.functions.owner().call()
    print(f"\nOwnership:")
    print(f"Contract Owner: {owner}")
    print(f"Are we owner? {'✓' if owner.lower() == account.address.lower() else '✗'}")
    
    # Check token prices
    tokens = {
        'WETH': os.getenv('WETH_ADDRESS'),
        'USDC': os.getenv('USDC_ADDRESS')
    }
    
    print("\nPrice Feed Status:")
    for name, token in tokens.items():
        print(f"\n{name} ({token}):")
        try:
            # Get price feed info
            price_info = mock_feed.functions.getPriceFeedInfo(token).call()
            print(f"Raw Price: {price_info[0]}")
            print(f"Decimals: {price_info[1]}")
            print(f"Active: {'✓' if price_info[2] else '✗'}")
            
            if price_info[2]:  # If active
                # Get latest price
                price, timestamp = mock_feed.functions.getLatestPrice(token).call()
                print(f"Latest Price: ${price/10**8:.2f}")
                print(f"Last Updated: {timestamp}")
        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == '__main__':
    main()
