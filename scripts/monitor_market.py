import asyncio
import json
import logging
from web3 import Web3
from decimal import Decimal
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/market_monitor.log'),
        logging.StreamHandler()
    ]
)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Connect to Base
w3 = Web3(Web3.HTTPProvider(config['base_rpc_url']))

# Load contracts
with open('deployments/MarketMonitor.json', 'r') as f:
    market_monitor = json.load(f)

# Contract instance
market_monitor_contract = w3.eth.contract(
    address=market_monitor['address'],
    abi=market_monitor['abi']
)


async def update_gas_data():
    """Update gas price data"""
    try:
        # Get gas prices
        base_fee = w3.eth.get_block('latest').baseFeePerGas
        max_priority_fee = w3.eth.max_priority_fee
        
        # Calculate gas prices
        slow_gas = base_fee + (max_priority_fee // 2)
        standard_gas = base_fee + max_priority_fee
        fast_gas = base_fee + (max_priority_fee * 2)
        
        # Update contract
        tx = market_monitor_contract.functions.updateGas(
            fast_gas,
            standard_gas,
            slow_gas,
            base_fee
        ).build_transaction({
            'from': config['account_address'],
            'nonce': w3.eth.get_transaction_count(config['account_address']),
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, config['private_key'])
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            logging.info('Gas data updated:')
            logging.info(f'Base Fee: {w3.from_wei(base_fee, "gwei")} gwei')
            logging.info(f'Standard Gas: {w3.from_wei(standard_gas, "gwei")} gwei')
            logging.info(f'Fast Gas: {w3.from_wei(fast_gas, "gwei")} gwei')
        else:
            logging.error('Gas data update failed')
            
    except Exception as e:
        logging.error(f'Error updating gas data: {str(e)}')


async def update_volume_data(token0: str, token1: str, dex: str, amount: int):
    """Update volume data for a token pair on a DEX"""
    try:
        tx = market_monitor_contract.functions.updateVolume(
            token0,
            token1,
            dex,
            amount
        ).build_transaction({
            'from': config['account_address'],
            'nonce': w3.eth.get_transaction_count(config['account_address']),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, config['private_key'])
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            volume_data = market_monitor_contract.functions.getVolumeData(
                token0,
                token1,
                dex
            ).call()
            
            logging.info(f'Volume data updated for {token0}/{token1} on {dex}:')
            logging.info(f'24h Volume: {w3.from_wei(volume_data[0], "ether")} ETH')
            logging.info(f'Last Hour: {w3.from_wei(volume_data[1], "ether")} ETH')
        else:
            logging.error(f'Volume data update failed for {token0}/{token1} on {dex}')
            
    except Exception as e:
        logging.error(f'Error updating volume data: {str(e)}')


async def update_liquidity_data(
    token0: str,
    token1: str,
    dex: str,
    total_liquidity: int,
    utilization_rate: int,
    depth_points: List[int]
):
    """Update liquidity data for a token pair on a DEX"""
    try:
        tx = market_monitor_contract.functions.updateLiquidity(
            token0,
            token1,
            dex,
            total_liquidity,
            utilization_rate,
            depth_points
        ).build_transaction({
            'from': config['account_address'],
            'nonce': w3.eth.get_transaction_count(config['account_address']),
            'gas': 400000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, config['private_key'])
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            liquidity_data = market_monitor_contract.functions.getLiquidityData(
                token0,
                token1,
                dex
            ).call()
            
            logging.info(f'Liquidity data updated for {token0}/{token1} on {dex}:')
            logging.info(f'Total Liquidity: {w3.from_wei(liquidity_data[0], "ether")} ETH')
            logging.info(f'Utilization Rate: {liquidity_data[1] / 100}%')
        else:
            logging.error(f'Liquidity data update failed for {token0}/{token1} on {dex}')
            
    except Exception as e:
        logging.error(f'Error updating liquidity data: {str(e)}')


async def update_market_impact(token0: str, token1: str, dex: str, amount: int):
    """Update market impact data for a token pair on a DEX"""
    try:
        tx = market_monitor_contract.functions.updateMarketImpact(
            token0,
            token1,
            dex,
            amount
        ).build_transaction({
            'from': config['account_address'],
            'nonce': w3.eth.get_transaction_count(config['account_address']),
            'gas': 300000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, config['private_key'])
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            impact_data = market_monitor_contract.functions.getMarketImpact(
                token0,
                token1,
                dex
            ).call()
            
            logging.info(f'Market impact data updated for {token0}/{token1} on {dex}:')
            logging.info(f'Price Impact: {impact_data[0] / 100}%')
            logging.info(f'Slippage: {impact_data[1] / 100}%')
            logging.info(f'Volume Share: {impact_data[2] / 100}%')
        else:
            logging.error(f'Market impact update failed for {token0}/{token1} on {dex}')
            
    except Exception as e:
        logging.error(f'Error updating market impact: {str(e)}')


async def monitor_market():
    """Monitor market data"""
    while True:
        try:
            # Update gas data
            await update_gas_data()
            
            # Standard amount for monitoring (0.1 ETH)
            amount = w3.to_wei(0.1, 'ether')
            
            # Monitor all token pairs
            for token0 in config['tokens'].values():
                for token1 in config['tokens'].values():
                    if token0 != token1:
                        for dex_info in config['dexes'].values():
                            dex = dex_info['router']
                            
                            # Update volume
                            await update_volume_data(token0, token1, dex, amount)
                            
                            # Get liquidity info
                            total_liquidity = w3.to_wei(10, 'ether')  # Example value
                            utilization_rate = 7000  # 70%
                            depth_points = [
                                w3.to_wei(1, 'ether'),
                                w3.to_wei(2, 'ether'),
                                w3.to_wei(5, 'ether')
                            ]
                            
                            # Update liquidity
                            await update_liquidity_data(
                                token0,
                                token1,
                                dex,
                                total_liquidity,
                                utilization_rate,
                                depth_points
                            )
                            
                            # Update market impact
                            await update_market_impact(token0, token1, dex, amount)
            
            # Wait before next update
            await asyncio.sleep(config['update_interval'])
            
        except Exception as e:
            logging.error(f'Error in market monitoring: {str(e)}')
            await asyncio.sleep(5)


async def main():
    """Main function"""
    logging.info('Starting market monitor...')
    
    # Start monitoring
    await monitor_market()


if __name__ == '__main__':
    asyncio.run(main())
