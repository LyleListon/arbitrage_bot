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
    
    # Get token addresses
    weth = os.getenv('WETH_ADDRESS')
    usdc = os.getenv('USDC_ADDRESS')
    dex = os.getenv('UNISWAP_V2_ROUTER')
    
    print("\nSimulating Trade Parameters:")
    print(f"DEX: {dex}")
    print(f"WETH: {weth}")
    print(f"USDC: {usdc}")
    
    # Get current prices
    weth_price, _ = mock_feed.functions.getLatestPrice(weth).call()
    usdc_price, _ = mock_feed.functions.getLatestPrice(usdc).call()
    
    print(f"\nCurrent Prices:")
    print(f"WETH: ${weth_price/10**8:.2f}")
    print(f"USDC: ${usdc_price/10**8:.2f}")
    
    # Simulate trade path
    path = [weth, usdc]  # WETH -> USDC
    amount_in = w3.to_wei(0.1, 'ether')  # 0.1 ETH
    
    try:
        # Simulate trade
        amounts = bot.functions.simulateTrade(
            dex,
            amount_in,
            path
        ).call()
        
        print("\nTrade Simulation Results:")
        print(f"Input: {w3.from_wei(amounts[0], 'ether')} WETH")
        print(f"Output: {amounts[1] / 10**6} USDC")  # USDC has 6 decimals
        
        # Calculate expected profit
        weth_value_usd = w3.from_wei(amounts[0], 'ether') * weth_price/10**8
        usdc_value = amounts[1] / 10**6
        profit_usd = usdc_value - weth_value_usd
        profit_pct = (profit_usd / weth_value_usd) * 100
        
        print(f"\nProfit Analysis:")
        print(f"WETH Value: ${weth_value_usd:.2f}")
        print(f"USDC Value: ${usdc_value:.2f}")
        print(f"Profit: ${profit_usd:.2f} ({profit_pct:.2f}%)")
        
        # Check if trade would be profitable
        min_profit = bot.functions.minProfitBasisPoints().call() / 100  # Convert basis points to percentage
        print(f"\nProfitability Check:")
        print(f"Required Profit: {min_profit}%")
        print(f"Actual Profit: {profit_pct:.2f}%")
        print(f"Trade would be {'✓ executable' if profit_pct >= min_profit else '✗ not executable'}")
        
    except Exception as e:
        print(f"\nError simulating trade: {str(e)}")


if __name__ == '__main__':
    main()
