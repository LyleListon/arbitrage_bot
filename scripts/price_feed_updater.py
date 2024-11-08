from web3 import Web3
import time
import json
import os
import argparse
import requests
from database import save_price
from dotenv import load_dotenv

load_dotenv()

def get_network_config(network):
    configs = {
        'ethereum': {
            'rpc_url': os.getenv('ETHEREUM_RPC_URL'),
            'chain_id': 1,
        },
        'arbitrum': {
            'rpc_url': os.getenv('ARBITRUM_RPC_URL'),
            'chain_id': 42161,
        },
        'bsc': {
            'rpc_url': os.getenv('BSC_RPC_URL'),
            'chain_id': 56,
        }
    }
    return configs.get(network, configs['ethereum'])

def get_price(symbol, network):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
    response = requests.get(url)
    data = response.json()
    return int(data[symbol]['usd'] * 10**8)  # Convert to 8 decimal places

def update_prices(w3, contract, token_a_symbol, token_b_symbol, network):
    price_a = get_price(token_a_symbol, network)
    price_b = get_price(token_b_symbol, network)
    tx_hash = contract.functions.updatePrices(price_a, price_b).transact()
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    timestamp = int(time.time())
    save_price(network, token_a_symbol, price_a, timestamp)
    save_price(network, token_b_symbol, price_b, timestamp)
    
    return tx_receipt

def main(network):
    config = get_network_config(network)
    w3 = Web3(Web3.HTTPProvider(config['rpc_url']))

    private_key = os.getenv('PRIVATE_KEY')
    if not private_key:
        raise ValueError("Please set the PRIVATE_KEY environment variable")

    account = w3.eth.account.from_key(private_key)
    w3.eth.default_account = account.address

    with open('abi/ArbitrageBot.json', 'r') as file:
        contract_abi = json.load(file)
    
    contract_address = os.getenv(f'{network.upper()}_CONTRACT_ADDRESS')
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    token_a_symbol = os.getenv(f'{network.upper()}_TOKEN_A_SYMBOL')
    token_b_symbol = os.getenv(f'{network.upper()}_TOKEN_B_SYMBOL')

    while True:
        tx_receipt = update_prices(w3, contract, token_a_symbol, token_b_symbol, network)
        print(f"Prices updated. Transaction hash: {tx_receipt.transactionHash.hex()}")
        time.sleep(300)  # Update prices every 5 minutes

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update price feeds")
    parser.add_argument(
        '--network',
        choices=['ethereum', 'arbitrum', 'bsc'],
        default='ethereum',
        help="Network to run on"
    )
    args = parser.parse_args()

    main(args.network)
