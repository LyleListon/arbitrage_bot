from web3 import Web3
from dotenv import load_dotenv
import os
import time


def main():
    # Load mainnet configuration
    load_dotenv('.env.mainnet')
    w3 = Web3(Web3.HTTPProvider(os.getenv('MAINNET_RPC_URL')))
    print(f"Connected to mainnet: {w3.is_connected()}")
    
    # Check gas prices
    print("\nChecking gas prices...")
    for _ in range(3):  # Check 3 times over 30 seconds
        gas_price = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')
        block = w3.eth.get_block('latest')
        base_fee = w3.from_wei(block['baseFeePerGas'], 'gwei')
        
        print(f"\nBlock {block['number']}:")
        print(f"Base Fee: {base_fee:.2f} Gwei")
        print(f"Gas Price: {gas_price_gwei:.2f} Gwei")
        
        # Estimate deployment costs
        estimated_gas = {
            'PriceFeedIntegration': 1000000,
            'ArbitrageBot': 2000000,
            'Setup & Config': 500000
        }
        
        print("\nEstimated deployment costs:")
        total_cost = 0
        for contract, gas in estimated_gas.items():
            cost = w3.from_wei(gas * gas_price, 'ether')
            total_cost += cost
            print(f"{contract}: {cost:.4f} ETH")
        
        print(f"Total estimated cost: {total_cost:.4f} ETH")
        
        if _ < 2:  # Don't sleep on last iteration
            print("\nWaiting 15 seconds for next check...")
            time.sleep(15)
    
    # Check our balance
    account = w3.eth.account.from_key(os.getenv('MAINNET_PRIVATE_KEY'))
    balance = w3.eth.get_balance(account.address)
    print(f"\nDeployment wallet balance: {w3.from_wei(balance, 'ether'):.4f} ETH")
    print(f"Address: {account.address}")


if __name__ == '__main__':
    main()
