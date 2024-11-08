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
    
    print("\nContract Setup Verification")
    print("=" * 50)
    
    # 1. Contract Addresses
    print("\n1. Contract Addresses:")
    print(f"ArbitrageBot: {bot.address}")
    print(f"MockPriceFeed: {mock_feed.address}")
    
    # 2. Bot Parameters
    min_profit = bot.functions.minProfitBasisPoints().call()
    max_trade = bot.functions.maxTradeSize().call()
    withdrawal_delay = bot.functions.emergencyWithdrawalDelay().call()
    
    print("\n2. Bot Parameters:")
    print(f"Min Profit: {min_profit/100}%")
    print(f"Max Trade Size: {w3.from_wei(max_trade, 'ether')} ETH")
    print(f"Emergency Withdrawal Delay: {withdrawal_delay/3600} hours")
    
    # 3. Price Feeds
    tokens = {
        'WETH': os.getenv('WETH_ADDRESS'),
        'USDC': os.getenv('USDC_ADDRESS')
    }
    
    print("\n3. Price Feed Status:")
    for name, token in tokens.items():
        print(f"\n{name}:")
        print(f"Address: {token}")
        
        # Check bot authorization
        is_authorized = bot.functions.authorizedTokens(token).call()
        print(f"Bot Authorization: {'✓' if is_authorized else '✗'}")
        
        # Check price feed
        try:
            price, timestamp = mock_feed.functions.getLatestPrice(token).call()
            print(f"Price Feed: ${price/10**8:.2f}")
            print(f"Last Updated: {timestamp}")
            print(f"Feed Status: ✓ Active")
        except Exception as e:
            print(f"Feed Status: ✗ Error - {str(e)}")
    
    # 4. DEX Setup
    dex = os.getenv('UNISWAP_V2_ROUTER')
    is_authorized = bot.functions.authorizedDEXs(dex).call()
    
    print("\n4. DEX Configuration:")
    print(f"Uniswap V2: {dex}")
    print(f"Authorization: {'✓' if is_authorized else '✗'}")
    
    # 5. Contract State
    print("\n5. Contract State:")
    is_paused = bot.functions.paused().call()
    withdrawal_requested = bot.functions.emergencyWithdrawalRequested().call()
    print(f"Bot Paused: {'✓' if is_paused else '✗'}")
    print(f"Emergency Withdrawal Requested: {'✓' if withdrawal_requested else '✗'}")
    
    print("\nSetup Verification Complete!")
    print("=" * 50)
    print("\nNext Steps:")
    print("1. Deploy to mainnet using the same configuration")
    print("2. Set up mainnet price feeds with real Chainlink oracles")
    print("3. Start with small trade sizes and monitor closely")
    print("4. Have emergency procedures ready")


if __name__ == '__main__':
    main()
