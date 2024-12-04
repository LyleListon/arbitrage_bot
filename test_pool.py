from web3 import Web3
import json
import logging
from decimal import Decimal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_price_fetching():
    print("\n=== Testing Price Fetching with Current Config ===")
    
    # Connect to Base RPC
    w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
    print(f"Connected to Base: {w3.is_connected()}")
    
    # Load config
    with open('configs/dex_config.json', 'r') as f:
        config = json.load(f)
    
    # Get pool info
    pool_info = config['dexes']['uniswap_v3']['pools']['WETH/USDC']
    pool_address = Web3.to_checksum_address(pool_info['address'])
    
    # Load pool ABI
    with open('aero/cl100_weth_usdc_pool_abi.json', 'r') as f:
        pool_abi = json.load(f)
    
    # Initialize pool contract
    pool = w3.eth.contract(address=pool_address, abi=pool_abi)
    
    try:
        print("\nPool Information:")
        print(f"Address: {pool_address}")
        print(f"Token0: {pool_info['token0']}")
        print(f"Token1: {pool_info['token1']}")
        print(f"Fee: {pool_info['fee']} bps")
        
        print("\nFetching current price...")
        slot0 = pool.functions.slot0().call()
        sqrtPriceX96 = slot0[0]
        tick = slot0[1]
        
        # Calculate price from sqrtPriceX96
        price = (float(sqrtPriceX96) / (2**96)) ** 2
        
        # Adjust for decimals (USDC has 6, WETH has 18)
        price = price * (10**12)  # 18 - 6 = 12
        
        print(f"\nCurrent State:")
        print(f"- Price (USDC per WETH): {price}")
        print(f"- Tick: {tick}")
        
        # Calculate min/max trade sizes in USD
        min_trade_eth = float(config['tokens']['WETH']['min_amount'])
        max_trade_eth = float(config['pairs'][0]['max_trade_size'])
        
        min_trade_usd = min_trade_eth * price
        max_trade_usd = max_trade_eth * price
        
        print(f"\nTrade Size Limits:")
        print(f"- Minimum: {min_trade_eth} ETH (${min_trade_usd:.2f})")
        print(f"- Maximum: {max_trade_eth} ETH (${max_trade_usd:.2f})")
        
        # Get pool liquidity
        liquidity = pool.functions.liquidity().call()
        print(f"\nPool Liquidity: {liquidity}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Error type: {type(e)}")

if __name__ == "__main__":
    test_price_fetching()
