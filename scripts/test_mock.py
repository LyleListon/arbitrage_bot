"""
Test script for mock price feed and arbitrage bot
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
    
    # Load contracts
    mock_feed = load_contract(
        w3,
        'MockPriceFeed',
        os.getenv('HOLESKY_PRICE_FEED_ADDRESS')
    )
    
    arbitrage_bot = load_contract(
        w3,
        'ArbitrageBot',
        os.getenv('HOLESKY_BOT_ADDRESS')
    )
    
    # Test mock price feed
    print("\nTesting Mock Price Feed...")
    try:
        # Get WETH price
        weth_info = mock_feed.functions.getPriceFeedInfo(
            os.getenv('WETH_ADDRESS')
        ).call()
        print(f"\nWETH Price Feed:")
        print(f"Price: ${weth_info[0] / 10**8:.2f}")
        print(f"Decimals: {weth_info[1]}")
        print(f"Active: {weth_info[2]}")
        
        # Get USDC price
        usdc_info = mock_feed.functions.getPriceFeedInfo(
            os.getenv('USDC_ADDRESS')
        ).call()
        print(f"\nUSDC Price Feed:")
        print(f"Price: ${usdc_info[0] / 10**8:.2f}")
        print(f"Decimals: {usdc_info[1]}")
        print(f"Active: {usdc_info[2]}")
        
    except Exception as e:
        print(f"❌ Error testing price feed: {str(e)}")
    
    # Test arbitrage bot configuration
    print("\nTesting Arbitrage Bot Configuration...")
    try:
        # Check parameters
        min_profit = arbitrage_bot.functions.minProfitBasisPoints().call()
        max_trade = arbitrage_bot.functions.maxTradeSize().call()
        withdrawal_delay = arbitrage_bot.functions.emergencyWithdrawalDelay().call()
        
        print("\nBot Parameters:")
        print(f"Minimum Profit: {min_profit/100}%")
        print(f"Maximum Trade Size: {w3.from_wei(max_trade, 'ether')} ETH")
        print(f"Emergency Withdrawal Delay: {withdrawal_delay/3600} hours")
        
        # Check authorizations
        is_dex_authorized = arbitrage_bot.functions.authorizedDEXs(
            os.getenv('UNISWAP_V2_ROUTER')
        ).call()
        print(f"\nUniswap V2 Router authorized: {is_dex_authorized}")
        
        is_weth_authorized = arbitrage_bot.functions.authorizedTokens(
            os.getenv('WETH_ADDRESS')
        ).call()
        print(f"WETH authorized: {is_weth_authorized}")
        
        is_usdc_authorized = arbitrage_bot.functions.authorizedTokens(
            os.getenv('USDC_ADDRESS')
        ).call()
        print(f"USDC authorized: {is_usdc_authorized}")
        
    except Exception as e:
        print(f"❌ Error testing bot configuration: {str(e)}")
    
    # Test trade simulation
    print("\nTesting Trade Simulation...")
    try:
        # Set up trade parameters
        test_amount = w3.to_wei(0.01, 'ether')  # 0.01 ETH test trade
        path = [
            os.getenv('WETH_ADDRESS'),
            os.getenv('USDC_ADDRESS')
        ]
        
        # Simulate trade
        amounts = arbitrage_bot.functions.simulateTrade(
            os.getenv('UNISWAP_V2_ROUTER'),
            test_amount,
            path
        ).call()
        
        print(f"\nTrade Simulation Results:")
        print(f"Input: {w3.from_wei(amounts[0], 'ether')} WETH")
        print(f"Expected Output: {amounts[-1] / 1e6} USDC")
        
        # Calculate expected profit in USD
        weth_value_usd = w3.from_wei(test_amount, 'ether') * (weth_info[0] / 1e8)
        usdc_value = amounts[-1] / 1e6
        profit_usd = usdc_value - weth_value_usd
        profit_percentage = (profit_usd / weth_value_usd) * 100
        
        print(f"Expected Profit: ${profit_usd:.2f} ({profit_percentage:.2f}%)")
        
    except Exception as e:
        print(f"❌ Error simulating trade: {str(e)}")


if __name__ == "__main__":
    main()
