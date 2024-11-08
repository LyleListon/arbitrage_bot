import asyncio
import json
import logging
import time
from web3 import Web3
from eth_abi import encode
from decimal import Decimal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/price_monitor.log'),
        logging.StreamHandler()
    ]
)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Connect to Base
w3 = Web3(Web3.HTTPProvider(config['base_rpc_url']))

# Load contracts
with open('deployments/PriceMonitor.json', 'r') as f:
    price_monitor = json.load(f)

with open('deployments/DEXRegistry.json', 'r') as f:
    dex_registry = json.load(f)

# Contract instances
price_monitor_contract = w3.eth.contract(
    address=price_monitor['address'],
    abi=price_monitor['abi']
)

dex_registry_contract = w3.eth.contract(
    address=dex_registry['address'],
    abi=dex_registry['abi']
)

# Token addresses
TOKENS = {
    'WETH': '0x4200000000000000000000000000000000000006',
    'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
    'USDT': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb',
    'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb'
}

# DEX addresses
DEXES = {
    'BaseSwap': '0xfDf7b675D32D093E3cDD4261F52b448812EF9cD3',
    'UniswapV3': '0x2626664c2603336E57B271c5C0b26F421741e481',
    'SushiSwap': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
    'Aerodrome': '0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43'
}

async def update_price(token0, token1, dex, amount):
    """Update price for a token pair on a specific DEX"""
    try:
        tx = price_monitor_contract.functions.updatePrice(
            token0,
            token1,
            dex,
            amount
        ).build_transaction({
            'from': config['account_address'],
            'nonce': w3.eth.get_transaction_count(config['account_address']),
            'gas': 500000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, config['private_key'])
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            logging.info(f'Price updated for {token0}/{token1} on {dex}')
            
            # Check for arbitrage opportunities
            opportunities = price_monitor_contract.functions.getArbitrageOpportunities(
                token0,
                token1
            ).call()
            
            for opp in opportunities:
                logging.info(f'Arbitrage opportunity found:')
                logging.info(f'Buy DEX: {opp[0]}')
                logging.info(f'Sell DEX: {opp[1]}')
                logging.info(f'Spread: {Decimal(opp[2]) / 100}%')
                logging.info(f'Max Trade Size: {w3.from_wei(opp[3], "ether")} ETH')
                logging.info(f'Estimated Profit: {w3.from_wei(opp[4], "ether")} ETH')
        else:
            logging.error(f'Price update failed for {token0}/{token1} on {dex}')
            
    except Exception as e:
        logging.error(f'Error updating price: {str(e)}')

async def monitor_prices():
    """Monitor prices across all DEXs"""
    while True:
        try:
            # Standard amount for price check (0.1 ETH)
            amount = w3.to_wei(0.1, 'ether')
            
            # Check all token pairs
            for token0 in TOKENS.values():
                for token1 in TOKENS.values():
                    if token0 != token1:
                        for dex in DEXES.values():
                            await update_price(token0, token1, dex, amount)
            
            # Wait before next update
            await asyncio.sleep(config['update_interval'])
            
        except Exception as e:
            logging.error(f'Error in price monitoring: {str(e)}')
            await asyncio.sleep(5)

async def main():
    """Main function"""
    logging.info('Starting price monitor...')
    
    # Start monitoring
    await monitor_prices()

if __name__ == '__main__':
    asyncio.run(main())
