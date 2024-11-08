from web3 import Web3
from eth_abi import decode
import json

# Price Feed ABI - just what we need for testing
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
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def main():
    # Connect to Holesky
    w3 = Web3(Web3.HTTPProvider('https://ethereum-holesky.publicnode.com'))
    print(f"Connected to Holesky: {w3.is_connected()}")
    
    # Price feed addresses
    feeds = {
        'ETH/USD': '0x694AA1769357215DE4FAC081bf1f309aDC325306',
        'USDC/USD': '0x572dDec9087154dC5dfBB1546Bb62713147e0Ab0',
        'DAI/USD': '0x0d79df66BE487753B02D015Fb622DED7f0E9798d'
    }
    
    # Test each feed
    for name, address in feeds.items():
        print(f"\nTesting {name} feed at {address}")
        try:
            # Create contract instance
            feed = w3.eth.contract(address=address, abi=PRICE_FEED_ABI)
            
            # Get decimals
            decimals = feed.functions.decimals().call()
            print(f"Decimals: {decimals}")
            
            # Get latest price
            roundId, answer, startedAt, updatedAt, answeredInRound = feed.functions.latestRoundData().call()
            price = answer / 10 ** decimals
            
            print(f"Latest price: ${price:.2f}")
            print(f"Updated at: {updatedAt}")
            print(f"Round ID: {roundId}")
            
        except Exception as e:
            print(f"Error testing feed: {str(e)}")

if __name__ == '__main__':
    main()
