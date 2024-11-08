"""
Check mainnet wallet balance and gas prices
"""
from web3 import Web3
from dotenv import load_dotenv
import os


def main():
    # Load mainnet configuration
    load_dotenv('.env.mainnet')
    rpc_url = os.getenv('MAINNET_RPC_URL')
    if not rpc_url:
        raise ValueError("MAINNET_RPC_URL not found in environment")
    
    # Connect to mainnet
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    print(f"Connected to mainnet: {w3.is_connected()}")
    
    # Get deployment wallet address
    private_key = os.getenv('MAINNET_PRIVATE_KEY')
    if not private_key:
        raise ValueError("MAINNET_PRIVATE_KEY not found in environment")
    
    account = w3.eth.account.from_key(private_key)
    print(f"\nDeployment Wallet:")
    print(f"Address: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")
    
    # Get current gas prices
    gas_price = w3.eth.gas_price
    print(f"\nCurrent Gas Price: {w3.from_wei(gas_price, 'gwei')} Gwei")
    
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
    
    # Check if we have enough
    if w3.from_wei(balance, 'ether') >= total_cost * 1.2:  # 20% buffer
        print("\n✓ Sufficient balance for deployment")
    else:
        print("\n✗ Insufficient balance for deployment")
        needed = total_cost * 1.2 - w3.from_wei(balance, 'ether')
        print(f"Need {needed:.4f} more ETH")


if __name__ == '__main__':
    main()
