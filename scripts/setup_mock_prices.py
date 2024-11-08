"""
Script to set up mock prices for testing
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
    
    # Load mock price feed contract
    mock_feed = load_contract(
        w3,
        'MockPriceFeed',
        os.getenv('HOLESKY_PRICE_FEED_ADDRESS')
    )
    
    # Set up mock prices
    try:
        # Set WETH price to $2000
        print("\nSetting WETH price...")
        weth_price = 2000 * 10**8  # $2000 with 8 decimals
        tx = mock_feed.functions.setPrice(
            os.getenv('WETH_ADDRESS'),
            weth_price,
            8  # decimals
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✅ WETH price set successfully")
        else:
            print("❌ Failed to set WETH price")
        
        # Set USDC price to $1
        print("\nSetting USDC price...")
        usdc_price = 1 * 10**8  # $1 with 8 decimals
        tx = mock_feed.functions.setPrice(
            os.getenv('USDC_ADDRESS'),
            usdc_price,
            8  # decimals
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✅ USDC price set successfully")
        else:
            print("❌ Failed to set USDC price")
        
        # Verify prices
        print("\nVerifying prices...")
        weth_info = mock_feed.functions.getPriceFeedInfo(
            os.getenv('WETH_ADDRESS')
        ).call()
        print(f"WETH Price: ${weth_info[0] / 10**8:.2f}")
        print(f"WETH Decimals: {weth_info[1]}")
        print(f"WETH Feed Active: {weth_info[2]}")
        
        usdc_info = mock_feed.functions.getPriceFeedInfo(
            os.getenv('USDC_ADDRESS')
        ).call()
        print(f"USDC Price: ${usdc_info[0] / 10**8:.2f}")
        print(f"USDC Decimals: {usdc_info[1]}")
        print(f"USDC Feed Active: {usdc_info[2]}")
        
    except Exception as e:
        print(f"❌ Error setting up mock prices: {str(e)}")


if __name__ == "__main__":
    main()
