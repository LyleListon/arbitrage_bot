from web3 import Web3
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Connect to Holesky
rpc_url = os.getenv('HOLESKY_RPC_URL')
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Chainlink Price Feed ABI (minimal version for testing)
PRICE_FEED_ABI = [
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

def test_price_feed(feed_address, name):
    print(f"\nTesting {name} price feed at {feed_address}")
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(feed_address),
            abi=PRICE_FEED_ABI
        )
        roundId, answer, startedAt, updatedAt, answeredInRound = (
            contract.functions.latestRoundData().call()
        )
        price = answer / 10**8  # Chainlink prices typically have 8 decimals
        print(f"Latest price: ${price:,.2f}")
        print(f"Updated at: {updatedAt}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    print(f"Connected to network: {w3.is_connected()}")
    print(f"Chain ID: {w3.eth.chain_id}")
    
    # Test ETH/USD feed
    eth_feed = os.getenv('HOLESKY_ETH_USD_FEED')
    eth_success = test_price_feed(eth_feed, "ETH/USD")
    
    # Test USDC/USD feed
    usdc_feed = os.getenv('HOLESKY_USDC_USD_FEED')
    usdc_success = test_price_feed(usdc_feed, "USDC/USD")
    
    # Load and test our PriceFeedIntegration contract
    with open('abi/PriceFeedIntegration.json', 'r') as f:
        price_feed_abi = json.load(f)
    
    price_feed_address = os.getenv('HOLESKY_PRICE_FEED_ADDRESS')
    print(f"\nTesting PriceFeedIntegration contract at {price_feed_address}")
    
    try:
        price_feed = w3.eth.contract(
            address=Web3.to_checksum_address(price_feed_address),
            abi=price_feed_abi
        )
        
        # Test with WETH and USDC addresses
        weth_address = os.getenv('HOLESKY_WETH')
        usdc_address = os.getenv('HOLESKY_USDC')
        
        print(f"Getting prices for WETH ({weth_address}) and USDC ({usdc_address})")
        price_a, price_b = price_feed.functions.getLatestPrices(
            Web3.to_checksum_address(weth_address),
            Web3.to_checksum_address(usdc_address)
        ).call()
        
        print(f"Price A: {price_a}")
        print(f"Price B: {price_b}")
        
    except Exception as e:
        print(f"Error testing PriceFeedIntegration: {str(e)}")

if __name__ == "__main__":
    main()
