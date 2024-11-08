from web3 import Web3
from dotenv import load_dotenv
import json
import os
import time


def load_contract(w3, name, address):
    """Load contract ABI and create contract instance"""
    with open(f'abi/{name}.json', 'r') as f:
        abi = json.load(f)
    return w3.eth.contract(address=address, abi=abi)


def estimate_gas_with_buffer(w3, tx, from_address):
    """Estimate gas with safety buffer"""
    try:
        gas_estimate = w3.eth.estimate_gas({
            **tx,
            'from': from_address
        })
        return int(gas_estimate * 1.2)  # Add 20% buffer
    except Exception as e:
        print(f"Gas estimation failed: {str(e)}")
        return 200000  # Default gas limit


def main():
    # Load environment and connect to Holesky
    load_dotenv('.env.holesky')
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    print(f"Connected to Holesky: {w3.is_connected()}")
    
    # Load account
    account = w3.eth.account.from_key(os.getenv('HOLESKY_PRIVATE_KEY'))
    print(f"Using account: {account.address}")
    
    # Load mock feed contract
    mock_feed = load_contract(w3, 'MockPriceFeed', os.getenv('HOLESKY_PRICE_FEED_ADDRESS'))
    print(f"MockPriceFeed contract: {mock_feed.address}")
    
    # Verify ownership
    owner = mock_feed.functions.owner().call()
    if owner.lower() != account.address.lower():
        raise Exception("Not contract owner")
    print("✓ Ownership verified")
    
    # Token prices (with 8 decimals)
    token_prices = {
        'WETH': (os.getenv('WETH_ADDRESS'), int(2000 * 10**8)),  # $2000
        'USDC': (os.getenv('USDC_ADDRESS'), int(1 * 10**8))      # $1
    }
    
    # Set up each price feed
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    for name, (token, price) in token_prices.items():
        print(f"\nSetting up {name} price feed:")
        print(f"Token: {token}")
        print(f"Price: ${price/10**8:.2f}")
        
        try:
            # Build transaction
            tx = mock_feed.functions.setPrice(
                token,
                price,
                8  # 8 decimals for all prices
            ).build_transaction({
                'chainId': w3.eth.chain_id,
                'from': account.address,
                'nonce': nonce,
                'gasPrice': gas_price
            })
            
            # Estimate gas
            gas_limit = estimate_gas_with_buffer(w3, tx, account.address)
            tx['gas'] = gas_limit
            
            print(f"Transaction details:")
            print(f"Gas Price: {w3.from_wei(gas_price, 'gwei')} Gwei")
            print(f"Gas Limit: {gas_limit}")
            print(f"Estimated Cost: {w3.from_wei(gas_price * gas_limit, 'ether')} ETH")
            
            # Sign and send transaction
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            print("Waiting for confirmation...")
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
            if receipt.status == 1:
                print(f"✓ Price feed set successfully")
                print(f"Gas Used: {receipt.gasUsed}")
                print(f"Actual Cost: {w3.from_wei(receipt.gasUsed * gas_price, 'ether')} ETH")
            else:
                print(f"✗ Transaction failed")
                print(f"Receipt: {receipt}")
            
            # Verify price was set
            price_info = mock_feed.functions.getPriceFeedInfo(token).call()
            print(f"\nVerification:")
            print(f"Price: ${price_info[0]/10**8:.2f}")
            print(f"Decimals: {price_info[1]}")
            print(f"Active: {'✓' if price_info[2] else '✗'}")
            
            nonce += 1
            time.sleep(5)  # Wait between transactions
            
        except Exception as e:
            print(f"Error setting price feed: {str(e)}")
            print("Trying to diagnose the issue...")
            
            try:
                # Check if token is valid
                print("\nToken checks:")
                print(f"Token address valid: {'✓' if w3.is_address(token) else '✗'}")
                print(f"Token is not zero: {'✓' if token != '0x0000000000000000000000000000000000000000' else '✗'}")
                
                # Check if price is valid
                print("\nPrice checks:")
                print(f"Price is positive: {'✓' if price > 0 else '✗'}")
                print(f"Price in range: {'✓' if price < 2**256 else '✗'}")
                
            except Exception as diagnostic_error:
                print(f"Diagnostic error: {str(diagnostic_error)}")
            
            # Continue with next token
            nonce += 1
            continue


if __name__ == '__main__':
    main()
