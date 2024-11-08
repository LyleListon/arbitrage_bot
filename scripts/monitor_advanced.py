import asyncio
import json
import logging
import numpy as np
from web3 import Web3
from typing import List, Tuple
from scipy import stats
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/advanced_monitor.log'),
        logging.StreamHandler()
    ]
)

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Connect to Base
w3 = Web3(Web3.HTTPProvider(config['base_rpc_url']))

# Load contracts
with open('deployments/AdvancedMonitor.json', 'r') as f:
    advanced_monitor = json.load(f)

# Contract instance
monitor_contract = w3.eth.contract(
    address=advanced_monitor['address'],
    abi=advanced_monitor['abi']
)


def calculate_volatility(prices: List[float]) -> float:
    """Calculate price volatility using standard deviation"""
    if len(prices) < 2:
        return 0
    return float(np.std(prices))


def calculate_correlation(prices1: List[float], prices2: List[float]) -> Tuple[float, float]:
    """Calculate correlation and strength between two price series"""
    if len(prices1) < 2 or len(prices2) < 2:
        return 0, 0
        
    correlation, p_value = stats.pearsonr(prices1, prices2)
    strength = abs(correlation)
    
    return correlation, strength


def calculate_trend(prices: List[float], periods: int) -> int:
    """Calculate trend direction and strength"""
    if len(prices) < periods:
        return 0
        
    recent_prices = prices[-periods:]
    slope, _, r_value, _, _ = stats.linregress(range(len(recent_prices)), recent_prices)
    
    # Determine trend direction
    if slope > 0 and r_value > 0.7:
        return 1  # Up trend
    elif slope < 0 and r_value > 0.7:
        return -1  # Down trend
    return 0  # Sideways


async def update_volatility(token0: str, token1: str, dex: str, prices: List[float]):
    """Update volatility metrics"""
    try:
        tx = monitor_contract.functions.updateVolatility(
            token0,
            token1,
            dex,
            w3.to_wei(prices[-1], 'ether')
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
            volatility = calculate_volatility(prices)
            logging.info(f'Volatility updated for {token0}/{token1} on {dex}:')
            logging.info(f'Current Volatility: {volatility:.4f}')
        else:
            logging.error(f'Volatility update failed for {token0}/{token1} on {dex}')
            
    except Exception as e:
        logging.error(f'Error updating volatility: {str(e)}')


async def update_correlations(dex1: str, dex2: str, prices1: List[float], prices2: List[float]):
    """Update DEX correlation metrics"""
    try:
        correlation, strength = calculate_correlation(prices1, prices2)
        
        tx = monitor_contract.functions.updateDEXCorrelation(
            dex1,
            dex2,
            [w3.to_wei(p, 'ether') for p in prices1],
            [w3.to_wei(p, 'ether') for p in prices2]
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
            logging.info(f'Correlation updated between {dex1} and {dex2}:')
            logging.info(f'Correlation: {correlation:.4f}')
            logging.info(f'Strength: {strength:.4f}')
        else:
            logging.error(f'Correlation update failed for {dex1} and {dex2}')
            
    except Exception as e:
        logging.error(f'Error updating correlation: {str(e)}')


async def update_trends(token0: str, token1: str, dex: str, prices: List[float]):
    """Update trend metrics"""
    try:
        tx = monitor_contract.functions.updateTrend(
            token0,
            token1,
            dex,
            [w3.to_wei(p, 'ether') for p in prices]
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
            short_trend = calculate_trend(prices, 12)  # 1 hour
            medium_trend = calculate_trend(prices, 24) # 2 hours
            long_trend = calculate_trend(prices, 100)  # ~8 hours
            
            logging.info(f'Trends updated for {token0}/{token1} on {dex}:')
            logging.info(f'Short Trend: {short_trend}')
            logging.info(f'Medium Trend: {medium_trend}')
            logging.info(f'Long Trend: {long_trend}')
        else:
            logging.error(f'Trend update failed for {token0}/{token1} on {dex}')
            
    except Exception as e:
        logging.error(f'Error updating trends: {str(e)}')


async def monitor_advanced():
    """Monitor advanced market metrics"""
    while True:
        try:
            # Get price histories
            price_histories = {}
            for token0 in config['tokens'].values():
                for token1 in config['tokens'].values():
                    if token0 != token1:
                        pair_history = {}
                        for dex_info in config['dexes'].values():
                            dex = dex_info['router']
                            
                            # Get volatility data
                            volatility_data = monitor_contract.functions.getVolatilityData(
                                token0,
                                token1,
                                dex
                            ).call()
                            
                            prices = [float(w3.from_wei(p, 'ether')) for p in volatility_data[4]]
                            pair_history[dex] = prices
                            
                            # Update volatility
                            if prices:
                                await update_volatility(token0, token1, dex, prices)
                            
                        price_histories[(token0, token1)] = pair_history
            
            # Update correlations between DEXs
            dex_list = list(config['dexes'].values())
            for i in range(len(dex_list)):
                for j in range(i + 1, len(dex_list)):
                    dex1 = dex_list[i]['router']
                    dex2 = dex_list[j]['router']
                    
                    # Get price histories for correlation
                    for token0, token1 in price_histories:
                        if dex1 in price_histories[(token0, token1)] and dex2 in price_histories[(token0, token1)]:
                            prices1 = price_histories[(token0, token1)][dex1]
                            prices2 = price_histories[(token0, token1)][dex2]
                            
                            if prices1 and prices2:
                                await update_correlations(dex1, dex2, prices1, prices2)
            
            # Update trends
            for (token0, token1), pair_history in price_histories.items():
                for dex, prices in pair_history.items():
                    if prices:
                        await update_trends(token0, token1, dex, prices)
            
            # Wait before next update
            await asyncio.sleep(config['update_interval'])
            
        except Exception as e:
            logging.error(f'Error in advanced monitoring: {str(e)}')
            await asyncio.sleep(5)


async def main():
    """Main function"""
    logging.info('Starting advanced market monitor...')
    
    # Start monitoring
    await monitor_advanced()


if __name__ == '__main__':
    asyncio.run(main())
