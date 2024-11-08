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
    
    # Get our address
    our_address = w3.eth.account.from_key(os.getenv('HOLESKY_PRIVATE_KEY')).address
    print(f"\nOur address: {our_address}")
    
    # Load mock feed contract
    mock_feed_address = os.getenv('HOLESKY_PRICE_FEED_ADDRESS')
    mock_feed = load_contract(w3, 'MockPriceFeed', mock_feed_address)
    print(f"MockPriceFeed address: {mock_feed_address}")
    
    # Check owner
    try:
        owner = mock_feed.functions.owner().call()
        print(f"Contract owner: {owner}")
        print(f"Are we the owner? {'✓' if owner.lower() == our_address.lower() else '✗'}")
    except Exception as e:
        print(f"Error checking owner: {str(e)}")
    
    # Check deployment info
    try:
        with open('deployments/MockPriceFeed_holesky.json', 'r') as f:
            deployment = json.load(f)
            print("\nDeployment Info:")
            print(f"Deployer: {deployment['deployer']}")
            print(f"Timestamp: {deployment['timestamp']}")
            print(f"Transaction: {deployment['transaction_hash']}")
    except Exception as e:
        print(f"\nError reading deployment info: {str(e)}")


if __name__ == '__main__':
    main()
