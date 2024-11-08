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
    # Load Holesky configuration
    load_dotenv('.env.holesky')
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    print(f"Connected to Holesky: {w3.is_connected()}")
    
    # Load contracts
    mock_feed = load_contract(w3, 'MockPriceFeed', '0x3e6Ff3BC62a947925f5Ed334D41B662D899F2E92')
    bot = load_contract(w3, 'ArbitrageBot', '0xA46e02903BF0326516b986060c5e2d87e1895085')
    
    print("\nContract Setup Verification")
    print("=" * 50)
    
    # 1. Contract Addresses
    print("\n1. Contract Addresses:")
    print(f"MockPriceFeed: {mock_feed.address}")
    print(f"ArbitrageBot: {bot.address}")
    
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
        'WETH': Web3.to_checksum_address('0x94373a4919B3240D86eA41593D5eBa789FEF3848'),
        'USDC': Web3.to_checksum_address('0x9C4073e98dA7d92427B550Dc10e919dC54C3a61F')
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
            price_info = mock_feed.functions.getPriceFeedInfo(token).call()
            print(f"Price: ${price_info[0]/10**price_info[1]:.2f}")
            print(f"Decimals: {price_info[1]}")
            print(f"Active: {'✓' if price_info[2] else '✗'}")
        except Exception as e:
            print(f"Error getting price: {str(e)}")
    
    # 4. DEX Setup
    dex = Web3.to_checksum_address('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')
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


if __name__ == '__main__':
    main()
