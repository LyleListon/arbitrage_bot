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
    
    # Load account
    account = w3.eth.account.from_key(os.getenv('HOLESKY_PRIVATE_KEY'))
    print(f"Using account: {account.address}")
    
    # Load contracts
    bot = load_contract(w3, 'ArbitrageBot', os.getenv('HOLESKY_BOT_ADDRESS'))
    mock_feed = load_contract(w3, 'MockPriceFeed', os.getenv('HOLESKY_PRICE_FEED_ADDRESS'))
    
    print("\nContract Addresses:")
    print(f"ArbitrageBot: {bot.address}")
    print(f"MockPriceFeed: {mock_feed.address}")
    
    # Verify bot ownership
    bot_owner = bot.functions.owner().call()
    if bot_owner.lower() != account.address.lower():
        raise Exception("Not bot owner")
    print("✓ Bot ownership verified")
    
    # Verify feed ownership
    feed_owner = mock_feed.functions.owner().call()
    if feed_owner.lower() != account.address.lower():
        raise Exception("Not feed owner")
    print("✓ Feed ownership verified")
    
    # Update bot configuration
    tokens = {
        'WETH': os.getenv('WETH_ADDRESS'),
        'USDC': os.getenv('USDC_ADDRESS')
    }
    
    # Authorize tokens and verify prices
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    for name, token in tokens.items():
        print(f"\nSetting up {name}:")
        print(f"Token: {token}")
        
        # Verify price feed
        price, timestamp = mock_feed.functions.getLatestPrice(token).call()
        print(f"Price Feed: ${price/10**8:.2f}")
        print(f"Last Updated: {timestamp}")
        
        # Authorize token in bot
        try:
            tx = bot.functions.setAuthorizedToken(
                token,
                True
            ).build_transaction({
                'chainId': w3.eth.chain_id,
                'from': account.address,
                'nonce': nonce,
                'gasPrice': gas_price,
                'gas': 200000
            })
            
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Authorization tx sent: {tx_hash.hex()}")
            
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                print("✓ Token authorized")
            else:
                print("✗ Token authorization failed")
            
            nonce += 1
            
        except Exception as e:
            print(f"Error authorizing token: {str(e)}")
    
    # Authorize DEX
    dex = os.getenv('UNISWAP_V2_ROUTER')
    print(f"\nAuthorizing DEX:")
    print(f"Address: {dex}")
    
    try:
        tx = bot.functions.setAuthorizedDEX(
            dex,
            True
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 200000
        })
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"DEX authorization tx sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✓ DEX authorized")
        else:
            print("✗ DEX authorization failed")
        
    except Exception as e:
        print(f"Error authorizing DEX: {str(e)}")
    
    print("\nSetup complete!")


if __name__ == '__main__':
    main()
