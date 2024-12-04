from web3 import Web3
import json
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeSimulator:
    def __init__(self):
        # Connect to Base
        self.w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        logger.info(f"Connected to Base: {self.w3.is_connected()}")
        
        # Load configurations
        with open('configs/dex_config.json', 'r') as f:
            self.config = json.load(f)
        
        # Load ABIs
        with open('abi/IUniswapV3QuoterV2.json', 'r') as f:
            self.quoter_abi = json.load(f)
        with open('abi/ERC20.json', 'r') as f:
            self.erc20_abi = json.load(f)
            
        # Initialize contracts
        self.quoter = self.w3.eth.contract(
            address=self.config['dexes']['uniswap_v3']['quoter'],
            abi=self.quoter_abi
        )
        
        # Get token contracts
        self.weth = self.w3.eth.contract(
            address=self.config['tokens']['WETH']['address'],
            abi=self.erc20_abi
        )
        self.usdc = self.w3.eth.contract(
            address=self.config['tokens']['USDC']['address'],
            abi=self.erc20_abi
        )
        
        # Get pool info
        self.pool_info = self.config['dexes']['uniswap_v3']['pools']['WETH/USDC']
        
    def check_balances(self, address: str) -> Dict[str, float]:
        """Check WETH and USDC balances for an address"""
        try:
            weth_balance = self.weth.functions.balanceOf(address).call()
            usdc_balance = self.usdc.functions.balanceOf(address).call()
            
            # Convert to human readable
            weth_human = weth_balance / 10**18
            usdc_human = usdc_balance / 10**6
            
            logger.info(f"\nBalances for {address}:")
            logger.info(f"WETH: {weth_human:.6f}")
            logger.info(f"USDC: {usdc_human:.2f}")
            
            return {
                'WETH': weth_human,
                'USDC': usdc_human
            }
            
        except Exception as e:
            logger.error(f"Error checking balances: {e}")
            return {'WETH': 0, 'USDC': 0}
            
    def simulate_trade(
        self,
        token_in: str,
        amount_in: float
    ) -> Optional[Tuple[float, float, float]]:
        """Simulate a trade and return expected output"""
        try:
            # Convert amount to contract units
            decimals_in = 18 if token_in == 'WETH' else 6
            amount_in_raw = int(amount_in * 10**decimals_in)
            
            # Get token addresses
            token_in_addr = self.config['tokens'][token_in]['address']
            token_out = 'USDC' if token_in == 'WETH' else 'WETH'
            token_out_addr = self.config['tokens'][token_out]['address']
            
            # Get quote
            quote = self.quoter.functions.quoteExactInputSingle((
                token_in_addr,          # tokenIn
                token_out_addr,         # tokenOut
                amount_in_raw,          # amountIn
                self.pool_info['fee'],  # fee
                0                       # sqrtPriceLimitX96 (0 for no limit)
            )).call()
            
            # Extract values from quote
            amount_out = quote[0]
            sqrt_price_x96_after = quote[1]
            tick_after = quote[2]
            gas_estimate = quote[3]
            
            # Convert amount_out to human readable
            decimals_out = 6 if token_in == 'WETH' else 18
            amount_out_human = amount_out / 10**decimals_out
            
            # Calculate price impact
            if token_in == 'WETH':
                price_before = (float(sqrt_price_x96_after) / (2**96)) ** 2 * (10**12)
                price_after = amount_out_human / amount_in
            else:
                price_before = amount_in / amount_out_human
                price_after = (float(sqrt_price_x96_after) / (2**96)) ** 2 * (10**12)
            
            price_impact = abs((price_after - price_before) / price_before) * 100
            
            logger.info(f"\nTrade Simulation:")
            logger.info(f"Input: {amount_in} {token_in}")
            logger.info(f"Expected Output: {amount_out_human:.6f} {token_out}")
            logger.info(f"Price Impact: {price_impact:.4f}%")
            logger.info(f"Estimated Gas: {gas_estimate}")
            
            return amount_out_human, price_impact, gas_estimate
            
        except Exception as e:
            logger.error(f"Error simulating trade: {e}")
            return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_trades.py <wallet_address>")
        return
        
    wallet = sys.argv[1]
    if not Web3.is_address(wallet):
        print("Invalid wallet address")
        return
        
    print("\n=== Trade Testing Tool ===")
    simulator = TradeSimulator()
    
    # Check balances
    balances = simulator.check_balances(wallet)
    
    # Simulate small test trades if we have balance
    if balances['WETH'] >= 0.1:
        print("\nSimulating WETH -> USDC trade (0.1 WETH)...")
        simulator.simulate_trade('WETH', 0.1)
    
    if balances['USDC'] >= 400:
        print("\nSimulating USDC -> WETH trade (400 USDC)...")
        simulator.simulate_trade('USDC', 400)
    
    print("\nTest complete!")

if __name__ == "__main__":
    main()
