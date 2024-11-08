"""
Test script for the deployed arbitrage bot
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
    arbitrage_bot = load_contract(
        w3,
        'ArbitrageBot',
        os.getenv('HOLESKY_BOT_ADDRESS')
    )
    price_feed = load_contract(
        w3,
        'PriceFeedIntegration',
        os.getenv('HOLESKY_PRICE_FEED_ADDRESS')
    )
    
    # Test price feed
    print("\nTesting Price Feed Integration...")
    try:
        weth_price = price_feed.functions.getLatestPrice(
            os.getenv('WETH_ADDRESS')
        ).call()
        print(f"WETH Price: ${weth_price[0] / 1e8:.2f}")
        
        usdc_price = price_feed.functions.getLatestPrice(
            os.getenv('USDC_ADDRESS')
        ).call()
        print(f"USDC Price: ${usdc_price[0] / 1e8:.2f}")
    except Exception as e:
        print(f"Error getting prices: {str(e)}")
    
    # Test arbitrage bot configuration
    print("\nTesting Arbitrage Bot Configuration...")
    try:
        # Check if DEX is authorized
        is_dex_authorized = arbitrage_bot.functions.authorizedDEXs(
            os.getenv('UNISWAP_V2_ROUTER')
        ).call()
        print(f"Uniswap V2 Router authorized: {is_dex_authorized}")
        
        # Check if tokens are authorized
        is_weth_authorized = arbitrage_bot.functions.authorizedTokens(
            os.getenv('WETH_ADDRESS')
        ).call()
        print(f"WETH authorized: {is_weth_authorized}")
        
        is_usdc_authorized = arbitrage_bot.functions.authorizedTokens(
            os.getenv('USDC_ADDRESS')
        ).call()
        print(f"USDC authorized: {is_usdc_authorized}")
        
        # Get bot parameters
        min_profit = arbitrage_bot.functions.minProfitBasisPoints().call()
        max_trade = arbitrage_bot.functions.maxTradeSize().call()
        withdrawal_delay = arbitrage_bot.functions.emergencyWithdrawalDelay().call()
        
        print("\nBot Parameters:")
        print(f"Minimum Profit: {min_profit/100}%")
        print(f"Maximum Trade Size: {w3.from_wei(max_trade, 'ether')} ETH")
        print(f"Emergency Withdrawal Delay: {withdrawal_delay/3600} hours")
        
    except Exception as e:
        print(f"Error checking bot configuration: {str(e)}")
    
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
        
        print(f"Trade Simulation Results:")
        print(f"Input: {w3.from_wei(amounts[0], 'ether')} WETH")
        print(f"Expected Output: {amounts[-1] / 1e6} USDC")
        
        # Calculate expected profit
        weth_value_usd = w3.from_wei(test_amount, 'ether') * (weth_price[0] / 1e8)
        usdc_value = amounts[-1] / 1e6
        profit_usd = usdc_value - weth_value_usd
        profit_percentage = (profit_usd / weth_value_usd) * 100
        
        print(f"Expected Profit: ${profit_usd:.2f} ({profit_percentage:.2f}%)")
        
    except Exception as e:
        print(f"Error simulating trade: {str(e)}")


if __name__ == "__main__":
    main()
