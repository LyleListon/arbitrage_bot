import json
import logging
import os
import signal
import sys
import time
import traceback
from decimal import Decimal
from typing import Dict, Optional, Tuple

from dotenv import load_dotenv
from eth_account import Account
from web3 import Web3

# Load environment variables from .env.mainnet
load_dotenv('.env.mainnet')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('arbitrage.log')
    ]
)
logger = logging.getLogger(__name__)

class ArbitrageBot:
    def __init__(self):
        """Initialize the arbitrage bot"""
        # Connect to Base
        rpc_url = os.getenv('BASE_RPC_URL', 'https://mainnet.base.org')
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        logger.info(f"Connected to Base: {self.w3.is_connected()}")
        
        # Load configurations
        with open('configs/dex_config.json', 'r') as f:
            self.config = json.load(f)
        
        # Load ABIs
        with open('abi/ERC20.json', 'r') as f:
            self.erc20_abi = json.load(f)
        with open('abi/IUniswapV3Router.json', 'r') as f:
            self.router_abi = json.load(f)
        with open('abi/IUniswapV3QuoterV2.json', 'r') as f:
            self.quoter_abi = json.load(f)
            
        # Get private key from environment
        self.private_key = os.getenv('PRIVATE_KEY')
        if not self.private_key:
            raise ValueError("PRIVATE_KEY not found in .env.mainnet")
            
        # Get account
        self.account = Account.from_key(self.private_key)
        self.address = self.account.address
        logger.info(f"Using address: {self.address}")
        
        # Initialize contracts
        self.weth = self.w3.eth.contract(
            address=self.config['tokens']['WETH']['address'],
            abi=self.erc20_abi
        )
        self.usdc = self.w3.eth.contract(
            address=self.config['tokens']['USDC']['address'],
            abi=self.erc20_abi
        )
        self.router = self.w3.eth.contract(
            address="0x2626664c2603336E57B271c5C0b26F421741e481",  # SwapRouter02 on Base
            abi=self.router_abi
        )
        self.quoter = self.w3.eth.contract(
            address=self.config['dexes']['uniswap_v3']['quoter'],
            abi=self.quoter_abi
        )
        
        # Initialize performance tracking
        self.total_profit_usdc = Decimal('0')
        self.total_gas_cost_eth = Decimal('0')
        self.trades_executed = 0
        self.start_time = time.time()
        
        # Load trading parameters
        self.min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.002'))  # 0.2%
        self.max_slippage = float(os.getenv('MAX_SLIPPAGE', '0.002'))  # 0.2%
        self.max_gas_price = int(float(os.getenv('MAX_GAS_PRICE', '5')) * 10**9)  # Convert GWEI to WEI
        self.gas_limit = int(os.getenv('GAS_LIMIT', '350000'))
        self.test_amount_weth = float(os.getenv('TEST_AMOUNT_WETH', '0.5'))
        self.test_amount_usdc = float(os.getenv('TEST_AMOUNT_USDC', '2000'))
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        logger.info("Arbitrage bot initialized successfully")
        logger.info(f"Min profit threshold: {self.min_profit_threshold*100:.3f}%")
        logger.info(f"Max slippage: {self.max_slippage*100:.3f}%")
        logger.info(f"Max gas price: {self.max_gas_price/10**9:.1f} GWEI")
        logger.info(f"Gas limit: {self.gas_limit}")
        logger.info(f"Test amount WETH: {self.test_amount_weth:.3f}")
        logger.info(f"Test amount USDC: {self.test_amount_usdc:.2f}")
        
    def handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("\nShutting down gracefully...")
        self.print_performance()
        sys.exit(0)
        
    def print_performance(self):
        """Print bot performance metrics"""
        runtime = Decimal(str(time.time() - self.start_time))
        hours = runtime / Decimal('3600')
        
        logger.info("\nPerformance Summary:")
        logger.info(f"Runtime: {float(hours):.2f} hours")
        logger.info(f"Total Profit: {float(self.total_profit_usdc):.2f} USDC")
        logger.info(f"Total Gas Cost: {float(self.total_gas_cost_eth):.6f} ETH")
        logger.info(f"Trades Executed: {self.trades_executed}")
        if self.trades_executed > 0:
            avg_profit = self.total_profit_usdc / Decimal(str(self.trades_executed))
            avg_gas = self.total_gas_cost_eth / Decimal(str(self.trades_executed))
            logger.info(f"Average Profit per Trade: {float(avg_profit):.2f} USDC")
            logger.info(f"Average Gas Cost per Trade: {float(avg_gas):.6f} ETH")
        if hours > Decimal('0'):
            profit_per_hour = self.total_profit_usdc / hours
            logger.info(f"Profit per Hour: {float(profit_per_hour):.2f} USDC")
            
    def get_quote(self, amount_in: float, is_weth_to_usdc: bool) -> Tuple[int, float, int]:
        """Get quote for swap"""
        try:
            # Convert amount to contract units
            decimals_in = 18 if is_weth_to_usdc else 6
            amount_in_raw = int(amount_in * 10**decimals_in)
            
            # Set token addresses based on direction
            token_in = self.weth.address if is_weth_to_usdc else self.usdc.address
            token_out = self.usdc.address if is_weth_to_usdc else self.weth.address
            
            # Create params struct
            params = {
                'tokenIn': token_in,
                'tokenOut': token_out,
                'amountIn': amount_in_raw,
                'fee': self.config['dexes']['uniswap_v3']['pools']['WETH/USDC']['fee'],
                'sqrtPriceLimitX96': 0
            }
            
            # Get quote
            try:
                quote = self.quoter.functions.quoteExactInputSingle(params).call()
                amount_out = quote[0]  # First return value is amountOut
                gas_estimate = quote[3]  # Fourth return value is gasEstimate
                
                # Calculate effective price and impact
                if is_weth_to_usdc:
                    # WETH -> USDC
                    amount_out_decimal = amount_out / 10**6  # Convert to USDC
                    effective_price = amount_out_decimal / amount_in  # USDC per WETH
                else:
                    # USDC -> WETH
                    amount_out_decimal = amount_out / 10**18  # Convert to WETH
                    effective_price = amount_in / amount_out_decimal  # USDC per WETH
                    
                expected_price = 3700  # Current approximate price
                price_impact = abs(1 - (effective_price / expected_price)) * 100
                
                logger.info(f"\nQuote details:")
                logger.info(f"Direction: {'WETH->USDC' if is_weth_to_usdc else 'USDC->WETH'}")
                logger.info(f"Amount in: {amount_in:.6f} {'WETH' if is_weth_to_usdc else 'USDC'}")
                logger.info(f"Amount out: {amount_out_decimal:.6f} {'USDC' if is_weth_to_usdc else 'WETH'}")
                logger.info(f"Effective price: {effective_price:.2f} USDC per WETH")
                logger.info(f"Expected price: {expected_price:.2f} USDC per WETH")
                logger.info(f"Price impact: {price_impact:.4f}%")
                logger.info(f"Gas estimate: {gas_estimate}")
                
                return amount_out, price_impact, gas_estimate
                
            except Exception as e:
                logger.error(f"Quote error: {str(e)}")
                logger.error(traceback.format_exc())
                return 0, 0, 0
                
        except Exception as e:
            logger.error(f"Error getting quote: {str(e)}")
            logger.error(traceback.format_exc())
            return 0, 0, 0
            
    def find_arbitrage_opportunity(self) -> Optional[Dict]:
        """Look for arbitrage opportunities"""
        try:
            logger.info("\nChecking for opportunities...")
            
            # Get current gas price
            gas_price = int(self.w3.eth.gas_price * 1.1)
            logger.info(f"Current gas price: {gas_price/10**9:.2f} GWEI")
            
            if gas_price > self.max_gas_price:
                logger.info(f"Gas price too high: {gas_price/10**9:.2f} GWEI > {self.max_gas_price/10**9:.2f} GWEI")
                return None
            
            # Get quotes for both directions
            test_amount_weth = self.test_amount_weth
            test_amount_usdc = self.test_amount_usdc
            
            # WETH -> USDC quote
            weth_to_usdc_out, impact1, gas1 = self.get_quote(test_amount_weth, True)
            if weth_to_usdc_out == 0:
                logger.error("Failed to get WETH -> USDC quote")
                return None
                
            # Check price impact
            max_price_impact = float(os.getenv('MAX_PRICE_IMPACT', '0.02'))  # 2%
            if impact1 > max_price_impact * 100:
                logger.debug(f"WETH -> USDC price impact too high: {impact1:.4f}% > {max_price_impact*100:.2f}%")
                return None
                
            # USDC -> WETH quote
            usdc_to_weth_out, impact2, gas2 = self.get_quote(test_amount_usdc, False)
            if usdc_to_weth_out == 0:
                logger.error("Failed to get USDC -> WETH quote")
                return None
                
            # Check price impact
            if impact2 > max_price_impact * 100:
                logger.debug(f"USDC -> WETH price impact too high: {impact2:.4f}% > {max_price_impact*100:.2f}%")
                return None
            
            # Calculate prices
            price1 = weth_to_usdc_out / (test_amount_weth * 10**6)  # USDC per WETH
            price2 = test_amount_usdc / (usdc_to_weth_out / 10**18)  # USDC per WETH
            
            # Calculate price difference
            price_diff = abs(price1 - price2)
            price_diff_percent = (price_diff / min(price1, price2)) * 100
            
            # Calculate gas costs
            gas_cost_eth = ((gas1 + gas2) * gas_price) / 10**18
            gas_cost_usdc = gas_cost_eth * ((price1 + price2) / 2)  # Convert to USDC using average price
            
            # Calculate potential profit
            if price1 > price2:
                potential_profit = test_amount_usdc * (price1/price2 - 1) - gas_cost_usdc
                profit_percent = (potential_profit / test_amount_usdc) * 100
            else:
                potential_profit = test_amount_weth * (price2/price1 - 1) * price1 - gas_cost_usdc
                profit_percent = (potential_profit / (test_amount_weth * price1)) * 100
            
            logger.info(f"\nPrices:")
            logger.info(f"WETH -> USDC: {price1:.2f} USDC per WETH (impact: {impact1:.4f}%)")
            logger.info(f"USDC -> WETH: {price2:.2f} USDC per WETH (impact: {impact2:.4f}%)")
            logger.info(f"Difference: {price_diff:.2f} USDC ({price_diff_percent:.4f}%)")
            logger.info(f"Gas cost: {gas_cost_usdc:.2f} USDC")
            logger.info(f"Potential profit: {potential_profit:.2f} USDC ({profit_percent:.4f}%)")
            
            # Check minimum profit threshold
            min_profit_threshold = float(os.getenv('MIN_PROFIT_THRESHOLD', '0.002'))  # 0.2%
            if profit_percent < min_profit_threshold * 100:
                logger.debug(f"Profit too low: {profit_percent:.4f}% < {min_profit_threshold*100:.4f}%")
                return None
                
            # Check minimum absolute profit
            min_profit_usdc = float(os.getenv('MIN_PROFIT_USDC', '3.0'))  # $3 minimum profit
            if potential_profit < min_profit_usdc:
                logger.debug(f"Absolute profit too low: {potential_profit:.2f} USDC < {min_profit_usdc:.2f} USDC")
                return None
            
            # Check if opportunity exists
            if profit_percent > min_profit_threshold * 100 and potential_profit > min_profit_usdc:
                logger.info(f"Found profitable opportunity!")
                logger.info(f"Expected profit: {potential_profit:.2f} USDC ({profit_percent:.4f}%)")
                logger.info(f"Gas cost: {gas_cost_usdc:.2f} USDC")
                logger.info(f"Price impacts: {impact1:.4f}% / {impact2:.4f}%")
                
                # Determine direction
                if price1 > price2:
                    return {
                        'direction': 'usdc_to_weth',
                        'price_diff_percent': price_diff_percent,
                        'amount_in': test_amount_usdc,
                        'expected_out': usdc_to_weth_out / 10**18,
                        'price_impact': impact2,
                        'gas_cost_usdc': gas_cost_usdc,
                        'potential_profit': potential_profit,
                        'profit_percent': profit_percent
                    }
                else:
                    return {
                        'direction': 'weth_to_usdc',
                        'price_diff_percent': price_diff_percent,
                        'amount_in': test_amount_weth,
                        'expected_out': weth_to_usdc_out / 10**6,
                        'price_impact': impact1,
                        'gas_cost_usdc': gas_cost_usdc,
                        'potential_profit': potential_profit,
                        'profit_percent': profit_percent
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding arbitrage opportunity: {e}")
            logger.error(traceback.format_exc())
            return None
            
    def execute_arbitrage(self, opportunity: Dict) -> bool:
        """Execute arbitrage trade"""
        try:
            # Check balances
            weth_balance = self.weth.functions.balanceOf(self.address).call()
            usdc_balance = self.usdc.functions.balanceOf(self.address).call()
            
            # Convert to human readable
            weth_human = weth_balance / 10**18
            usdc_human = usdc_balance / 10**6
            
            logger.info(f"\nCurrent balances:")
            logger.info(f"WETH: {weth_human:.6f}")
            logger.info(f"USDC: {usdc_human:.2f}")
            
            # Check if we have enough balance
            if opportunity['direction'] == 'weth_to_usdc':
                if weth_balance < opportunity['amount_in'] * 10**18:
                    logger.error("Insufficient WETH balance")
                    return False
                    
                # Check and approve WETH if needed
                allowance = self.weth.functions.allowance(
                    self.address,
                    self.router.address
                ).call()
                
                if allowance < opportunity['amount_in'] * 10**18:
                    logger.info("Approving WETH...")
                    approve_txn = self.weth.functions.approve(
                        self.router.address,
                        2**256 - 1  # Max approval
                    ).build_transaction({
                        'from': self.address,
                        'gas': 100000,
                        'gasPrice': int(self.w3.eth.gas_price * 1.1),
                        'nonce': self.w3.eth.get_transaction_count(self.address),
                    })
                    
                    signed_txn = self.w3.eth.account.sign_transaction(approve_txn, self.private_key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                    if receipt.status != 1:
                        logger.error("WETH approval failed")
                        return False
                        
                # Execute WETH -> USDC swap
                amount_in_raw = int(opportunity['amount_in'] * 10**18)
                min_amount_out = int(opportunity['expected_out'] * (1 - self.max_slippage) * 10**6)
                
            else:  # usdc_to_weth
                if usdc_balance < opportunity['amount_in'] * 10**6:
                    logger.error("Insufficient USDC balance")
                    return False
                    
                # Check and approve USDC if needed
                allowance = self.usdc.functions.allowance(
                    self.address,
                    self.router.address
                ).call()
                
                if allowance < opportunity['amount_in'] * 10**6:
                    logger.info("Approving USDC...")
                    approve_txn = self.usdc.functions.approve(
                        self.router.address,
                        2**256 - 1  # Max approval
                    ).build_transaction({
                        'from': self.address,
                        'gas': 100000,
                        'gasPrice': int(self.w3.eth.gas_price * 1.1),
                        'nonce': self.w3.eth.get_transaction_count(self.address),
                    })
                    
                    signed_txn = self.w3.eth.account.sign_transaction(approve_txn, self.private_key)
                    tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                    if receipt.status != 1:
                        logger.error("USDC approval failed")
                        return False
                        
                # Execute USDC -> WETH swap
                amount_in_raw = int(opportunity['amount_in'] * 10**6)
                min_amount_out = int(opportunity['expected_out'] * (1 - self.max_slippage) * 10**18)
                
            # Prepare swap parameters
            params = {
                'tokenIn': self.weth.address if opportunity['direction'] == 'weth_to_usdc' else self.usdc.address,
                'tokenOut': self.usdc.address if opportunity['direction'] == 'weth_to_usdc' else self.weth.address,
                'fee': self.config['dexes']['uniswap_v3']['pools']['WETH/USDC']['fee'],
                'recipient': self.address,
                'amountIn': amount_in_raw,
                'amountOutMinimum': min_amount_out,
                'sqrtPriceLimitX96': 0
            }
            
            # Build swap transaction
            swap_txn = self.router.functions.exactInputSingle(params).build_transaction({
                'from': self.address,
                'gas': self.gas_limit,
                'gasPrice': int(self.w3.eth.gas_price * 1.1),
                'nonce': self.w3.eth.get_transaction_count(self.address),
                'value': 0
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(swap_txn, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Swap transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.info("Swap successful!")
                
                # Check new balances
                new_weth_balance = self.weth.functions.balanceOf(self.address).call()
                new_usdc_balance = self.usdc.functions.balanceOf(self.address).call()
                
                # Calculate amounts changed
                weth_change = (new_weth_balance - weth_balance) / 10**18
                usdc_change = (new_usdc_balance - usdc_balance) / 10**6
                
                logger.info(f"\nTrade Summary:")
                if opportunity['direction'] == 'weth_to_usdc':
                    logger.info(f"WETH spent: {-weth_change:.6f}")
                    logger.info(f"USDC received: {usdc_change:.2f}")
                    logger.info(f"Effective price: {usdc_change/(-weth_change):.2f} USDC per WETH")
                else:
                    logger.info(f"USDC spent: {-usdc_change:.2f}")
                    logger.info(f"WETH received: {weth_change:.6f}")
                    logger.info(f"Effective price: {-usdc_change/weth_change:.2f} USDC per WETH")
                    
                logger.info(f"Gas used: {receipt.gasUsed}")
                gas_price = receipt.effectiveGasPrice
                logger.info(f"Gas price: {gas_price/10**9:.2f} GWEI")
                gas_cost = (receipt.gasUsed * gas_price) / 10**18
                logger.info(f"Gas cost: {gas_cost:.6f} ETH")
                
                # Update performance metrics
                self.trades_executed += 1
                self.total_gas_cost_eth += Decimal(str(gas_cost))
                self.total_profit_usdc += Decimal(str(opportunity['potential_profit']))
                
                return True
                
            else:
                logger.error("Swap failed!")
                logger.error(f"Transaction: {self.w3.eth.get_transaction(tx_hash)}")
                logger.error(f"Receipt: {receipt}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing arbitrage: {e}")
            logger.error(traceback.format_exc())
            return False
            
    def run(self):
        """Main bot loop"""
        logger.info("\nStarting arbitrage bot...")
        
        try:
            while True:
                # Look for opportunities
                opportunity = self.find_arbitrage_opportunity()
                
                if opportunity:
                    logger.info("\nFound arbitrage opportunity!")
                    if self.execute_arbitrage(opportunity):
                        logger.info("Arbitrage executed successfully!")
                    else:
                        logger.error("Failed to execute arbitrage")
                        
                    # Print current performance
                    self.print_performance()
                
                # Sleep between checks
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nBot stopped by user")
            self.print_performance()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            self.print_performance()

def main():
    bot = ArbitrageBot()
    bot.run()

if __name__ == "__main__":
    main()
