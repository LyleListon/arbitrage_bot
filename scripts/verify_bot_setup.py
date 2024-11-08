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
    
    # Load contracts
    bot = load_contract(w3, 'ArbitrageBot', os.getenv('HOLESKY_BOT_ADDRESS'))
    mock_feed = load_contract(w3, 'MockPriceFeed', os.getenv('HOLESKY_PRICE_FEED_ADDRESS'))
    
    print("\nContract Addresses:")
    print(f"ArbitrageBot: {bot.address}")
    print(f"MockPriceFeed: {mock_feed.address}")
    
    # Check bot parameters
    min_profit = bot.functions.minProfitBasisPoints().call()
    max_trade = bot.functions.maxTradeSize().call()
    withdrawal_delay = bot.functions.emergencyWithdrawalDelay().call()
    
    print("\nBot Configuration:")
    print(f"Min Profit: {min_profit/100}%")
    print(f"Max Trade Size: {w3.from_wei(max_trade, 'ether')} ETH")
    print(f"Emergency Withdrawal Delay: {withdrawal_delay/3600} hours")
    
    # Check token setup
    tokens = {
        'WETH': os.getenv('WETH_ADDRESS'),
        'USDC': os.getenv('USDC_ADDRESS')
    }
    
    print("\nToken Status:")
    for name, token in tokens.items():
        print(f"\n{name} ({token}):")
        
        # Check bot authorization
        is_authorized = bot.functions.authorizedTokens(token).call()
        print(f"Bot Authorization: {'✓' if is_authorized else '✗'}")
        
        # Check price feed
        try:
            price, timestamp = mock_feed.functions.getLatestPrice(token).call()
            print(f"Price Feed: ${price/10**8:.2f}")
            print(f"Last Updated: {timestamp}")
        except Exception as e:
            print(f"Price Feed Error: {str(e)}")
    
    # Check DEX authorization
    dex = os.getenv('UNISWAP_V2_ROUTER')
    is_authorized = bot.functions.authorizedDEXs(dex).call()
    print(f"\nDEX Status:")
    print(f"Uniswap V2 ({dex}): {'✓' if is_authorized else '✗'}")
    
    print("\nSetup Verification Complete!")


if __name__ == '__main__':
    main()
