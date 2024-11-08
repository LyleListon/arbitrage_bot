"""
Script to set up price feeds for the arbitrage bot
"""
from web3 import Web3
from eth_account import Account
import os
from dotenv import load_dotenv
import json


def load_contract(w3, contract_name, address):
    """Load contract ABI and return contract instance"""
    with open(f'abi/{contract_name}.json', 'r') as f:
        abi = json.load(f)
    return w3.eth.contract(address=address, abi=abi)


def verify_chainlink_feed(w3, feed_address):
    """Verify if Chainlink feed is accessible"""
    abi = [
        {
            "inputs": [],
            "name": "latestRoundData",
            "outputs": [
                {"name": "roundId", "type": "uint80"},
                {"name": "answer", "type": "int256"},
                {"name": "startedAt", "type": "uint256"},
                {"name": "updatedAt", "type": "uint256"},
                {"name": "answeredInRound", "type": "uint80"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    try:
        feed = w3.eth.contract(address=feed_address, abi=abi)
        data = feed.functions.latestRoundData().call()
        print(f"Feed data: Price = ${data[1] / 1e8:.2f}, Updated at: {data[3]}")
        return True
    except Exception as e:
        print(f"Error verifying Chainlink feed: {str(e)}")
        return False


def main():
    # Load environment variables
    load_dotenv('.env.holesky')
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    if not w3.is_connected():
        raise Exception("Failed to connect to network")
    
    print(f"Connected to network. Chain ID: {w3.eth.chain_id}")
    
    # Load account
    account = Account.from_key(os.getenv('HOLESKY_PRIVATE_KEY'))
    print(f"Using address: {account.address}")
    
    # Load price feed contract
    price_feed_address = os.getenv('HOLESKY_PRICE_FEED_ADDRESS')
    print(f"\nPrice Feed Contract: {price_feed_address}")
    
    price_feed = load_contract(
        w3,
        'PriceFeedIntegration',
        price_feed_address
    )
    
    # Verify ownership
    try:
        owner = price_feed.functions.owner().call()
        print(f"Contract owner: {owner}")
        print(f"Is caller owner? {owner.lower() == account.address.lower()}")
    except Exception as e:
        print(f"Error checking ownership: {str(e)}")
        return
    
    # Set up price feeds
    token_feeds = {
        os.getenv('WETH_ADDRESS'): os.getenv('ETH_USD_PRICE_FEED'),
        os.getenv('USDC_ADDRESS'): os.getenv('USDC_USD_PRICE_FEED')
    }
    
    print("\nVerifying Chainlink feeds...")
    for token, feed in token_feeds.items():
        print(f"\nChecking feed for token: {token}")
        if not verify_chainlink_feed(w3, feed):
            print("⚠️ Chainlink feed verification failed")
            continue
    
    print("\nSetting up price feeds...")
    for token, feed in token_feeds.items():
        try:
            print(f"\nSetting up feed for token: {token}")
            print(f"Using price feed: {feed}")
            
            # Check if feed is already active
            feed_info = price_feed.functions.getPriceFeedInfo(token).call()
            if feed_info[2]:  # isActive
                print("Feed already active, skipping...")
                continue
            
            # Estimate gas for the transaction
            gas_estimate = price_feed.functions.setPriceFeed(
                token,
                feed
            ).estimate_gas({'from': account.address})
            print(f"Estimated gas: {gas_estimate}")
            
            # Set up the price feed
            tx = price_feed.functions.setPriceFeed(
                token,
                feed
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': int(gas_estimate * 1.2),  # Add 20% buffer
                'gasPrice': w3.eth.gas_price
            })
            
            # Sign and send transaction
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            print(f"Transaction sent: {tx_hash.hex()}")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                print("✅ Price feed set successfully")
            else:
                print("❌ Failed to set price feed")
                print(f"Transaction receipt: {receipt}")
            
        except Exception as e:
            print(f"❌ Error setting price feed: {str(e)}")
    
    # Verify setup
    print("\nVerifying price feeds...")
    for token in token_feeds.keys():
        try:
            feed_info = price_feed.functions.getPriceFeedInfo(token).call()
            print(f"\nToken: {token}")
            print(f"Feed Address: {feed_info[0]}")
            print(f"Decimals: {feed_info[1]}")
            print(f"Active: {feed_info[2]}")
            
            if feed_info[2]:
                price, timestamp = price_feed.functions.getLatestPrice(token).call()
                print(f"Current Price: ${price / 1e8:.2f}")
                print(f"Last Updated: {timestamp}")
        except Exception as e:
            print(f"❌ Error verifying price feed: {str(e)}")


if __name__ == "__main__":
    main()
