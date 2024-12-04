from web3 import Web3
import json
import logging
from decimal import Decimal
import time
from eth_account import Account
import os
from dotenv import load_dotenv

# Load environment variables from .env.mainnet
load_dotenv('.env.mainnet')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradeExecutor:
    def __init__(self):
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
        
        # Using SwapRouter02 instead of Universal Router
        self.router = self.w3.eth.contract(
            address="0x2626664c2603336E57B271c5C0b26F421741e481",  # SwapRouter02 on Base
            abi=self.router_abi
        )
        logger.info(f"Using SwapRouter02: {self.router.address}")
        
    def get_quote(self, amount_in: float) -> tuple[int, float]:
        """Get quote for WETH -> USDC swap"""
        try:
            # Load quoter ABI
            with open('abi/IUniswapV3QuoterV2.json', 'r') as f:
                quoter_abi = json.load(f)
            
            # Initialize quoter contract
            quoter = self.w3.eth.contract(
                address=self.config['dexes']['uniswap_v3']['quoter'],
                abi=quoter_abi
            )
            
            # Convert amount to wei
            amount_in_wei = int(amount_in * 10**18)
            
            # Get quote
            quote = quoter.functions.quoteExactInputSingle((
                self.weth.address,          # tokenIn
                self.usdc.address,          # tokenOut
                amount_in_wei,              # amountIn
                self.config['dexes']['uniswap_v3']['pools']['WETH/USDC']['fee'],  # fee
                0                           # sqrtPriceLimitX96
            )).call()
            
            amount_out = quote[0]
            effective_price = amount_out / (amount_in * 10**6)  # Convert to USDC per WETH
            expected_price = 3600  # Approximate current market price
            price_impact = abs(1 - (effective_price / expected_price)) * 100
            
            logger.info(f"\nQuote received:")
            logger.info(f"Expected output: {amount_out / 10**6:.2f} USDC")
            logger.info(f"Effective price: {effective_price:.2f} USDC per WETH")
            logger.info(f"Price impact: {price_impact:.4f}%")
            
            return amount_out, price_impact
            
        except Exception as e:
            logger.error(f"Error getting quote: {e}")
            return 0, 0
        
    def check_balances(self):
        """Check WETH and USDC balances"""
        try:
            weth_balance = self.weth.functions.balanceOf(self.address).call()
            usdc_balance = self.usdc.functions.balanceOf(self.address).call()
            
            # Convert to human readable
            weth_human = weth_balance / 10**18
            usdc_human = usdc_balance / 10**6
            
            logger.info(f"\nBalances:")
            logger.info(f"WETH: {weth_human:.6f}")
            logger.info(f"USDC: {usdc_human:.2f}")
            
            return weth_balance, usdc_balance
            
        except Exception as e:
            logger.error(f"Error checking balances: {e}")
            return 0, 0
            
    def check_allowance(self):
        """Check if router has approval to spend WETH"""
        try:
            allowance = self.weth.functions.allowance(
                self.address,
                self.router.address
            ).call()
            
            logger.info(f"\nCurrent WETH allowance: {allowance / 10**18:.6f}")
            return allowance
            
        except Exception as e:
            logger.error(f"Error checking allowance: {e}")
            return 0
            
    def approve_weth(self, amount: int):
        """Approve router to spend WETH"""
        try:
            # Build approval transaction
            nonce = self.w3.eth.get_transaction_count(self.address)
            gas_price = int(self.w3.eth.gas_price * 1.1)
            
            # Check against max gas price setting
            max_gas_price = int(float(os.getenv('MAX_GAS_PRICE', '5')) * 10**9)  # Convert GWEI to WEI
            if gas_price > max_gas_price:
                raise ValueError(f"Gas price too high: {gas_price/10**9:.2f} GWEI > {max_gas_price/10**9:.2f} GWEI")
            
            approve_txn = self.weth.functions.approve(
                self.router.address,
                amount
            ).build_transaction({
                'from': self.address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(approve_txn, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Approval transaction sent: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 1:
                logger.info("Approval successful!")
            else:
                logger.error("Approval failed!")
                
            return receipt.status == 1
            
        except Exception as e:
            logger.error(f"Error approving WETH: {e}")
            return False
            
    def execute_swap(self, amount_in: float):
        """Execute WETH -> USDC swap"""
        try:
            amount_in_wei = int(amount_in * 10**18)
            
            # Get quote first
            amount_out, price_impact = self.get_quote(amount_in)
            if amount_out == 0:
                logger.error("Failed to get quote")
                return False
                
            # Check if price impact is too high
            max_slippage = float(os.getenv('MAX_SLIPPAGE', '0.002')) * 100
            if price_impact > max_slippage:
                logger.error(f"Price impact too high: {price_impact:.4f}% > {max_slippage:.4f}%")
                return False
            
            # Calculate minimum output with 0.5% slippage
            min_amount_out = int(amount_out * 0.995)  # 0.5% slippage tolerance
            
            # Get current balances
            weth_before, usdc_before = self.check_balances()
            
            # Prepare swap parameters
            params = {
                'tokenIn': self.weth.address,
                'tokenOut': self.usdc.address,
                'fee': self.config['dexes']['uniswap_v3']['pools']['WETH/USDC']['fee'],
                'recipient': self.address,
                'amountIn': amount_in_wei,
                'amountOutMinimum': min_amount_out,
                'sqrtPriceLimitX96': 0
            }
            
            # Build swap transaction
            nonce = self.w3.eth.get_transaction_count(self.address)
            gas_price = int(self.w3.eth.gas_price * 1.1)
            
            # Check against max gas price setting
            max_gas_price = int(float(os.getenv('MAX_GAS_PRICE', '5')) * 10**9)  # Convert GWEI to WEI
            if gas_price > max_gas_price:
                raise ValueError(f"Gas price too high: {gas_price/10**9:.2f} GWEI > {max_gas_price/10**9:.2f} GWEI")
            
            swap_txn = self.router.functions.exactInputSingle(params).build_transaction({
                'from': self.address,
                'gas': int(os.getenv('GAS_LIMIT', '300000')),
                'gasPrice': gas_price,
                'nonce': nonce,
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
                weth_after, usdc_after = self.check_balances()
                
                # Calculate amounts changed
                weth_used = (weth_before - weth_after) / 10**18
                usdc_received = (usdc_after - usdc_before) / 10**6
                
                logger.info(f"\nSwap Summary:")
                logger.info(f"WETH used: {weth_used:.6f}")
                logger.info(f"USDC received: {usdc_received:.2f}")
                logger.info(f"Effective price: {usdc_received/weth_used:.2f} USDC per WETH")
                logger.info(f"Gas used: {receipt.gasUsed}")
                logger.info(f"Gas price: {gas_price/10**9:.2f} GWEI")
                logger.info(f"Total gas cost: {(receipt.gasUsed * gas_price) / 10**18:.6f} ETH")
                
            else:
                logger.error("Swap failed!")
                logger.error(f"Transaction: {self.w3.eth.get_transaction(tx_hash)}")
                logger.error(f"Receipt: {receipt}")
                
            return receipt.status == 1
            
        except Exception as e:
            logger.error(f"Error executing swap: {e}")
            return False

def main():
    executor = TradeExecutor()
    
    # Check initial balances
    weth_balance, usdc_balance = executor.check_balances()
    
    # Check if we have enough WETH
    test_amount = 0.05
    if weth_balance < test_amount * 10**18:
        logger.error(f"Insufficient WETH balance for test trade of {test_amount} WETH")
        return
        
    # Check and set allowance if needed
    allowance = executor.check_allowance()
    if allowance < test_amount * 10**18:
        logger.info("\nApproving WETH...")
        if not executor.approve_weth(2**256 - 1):  # Max approval
            logger.error("Failed to approve WETH")
            return
            
    # Execute test trade
    logger.info(f"\nExecuting test trade of {test_amount} WETH -> USDC...")
    success = executor.execute_swap(test_amount)
    
    if success:
        logger.info("\nTest trade completed successfully!")
    else:
        logger.error("\nTest trade failed!")

if __name__ == "__main__":
    main()
