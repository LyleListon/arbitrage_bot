"""DEX interface for price monitoring and trading"""

import json
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from web3.contract import Contract
from web3 import Web3
from .web3_utils import Web3Manager, get_web3_manager

logger = logging.getLogger(__name__)

class DexInterface:
    """Interface for DEX interactions"""
    
    def __init__(self):
        self.web3_manager = get_web3_manager()
        self.dex_config = self._load_config()
        self.contracts: Dict[str, Dict[str, Contract]] = {}
        self._initialize_contracts()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load DEX configuration"""
        try:
            with open('configs/dex_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading DEX config: {e}")
            raise
    
    def _initialize_contracts(self) -> None:
        """Initialize DEX contracts"""
        try:
            # Load contract ABIs
            with open('abi/IUniswapV3Pool.json', 'r') as f:
                uniswap_pool_abi = json.load(f)
            with open('abi/aerodrome_pool.json', 'r') as f:
                aerodrome_pool_abi = json.load(f)
            with open('abi/IUniswapV3QuoterV2.json', 'r') as f:
                quoter_abi = json.load(f)
            
            # Initialize Uniswap V3 Quoter
            quoter_address = self.dex_config['dexes']['uniswap_v3']['quoter']
            self.uniswap_quoter = self.web3_manager.get_contract(quoter_address, quoter_abi)
            
            # Initialize pool contracts
            for dex_name, dex_info in self.dex_config['dexes'].items():
                self.contracts[dex_name] = {}
                
                for pair_name, pool_info in dex_info['pools'].items():
                    if 'address' not in pool_info:
                        logger.warning(f"No pool address for {dex_name} {pair_name}, skipping")
                        continue
                        
                    # Select appropriate ABI based on DEX type
                    abi = (
                        uniswap_pool_abi if dex_info['type'] == 'UniswapV3'
                        else aerodrome_pool_abi
                    )
                    
                    # Initialize contract with retry mechanism
                    self.contracts[dex_name][pair_name] = (
                        self.web3_manager.get_contract(pool_info['address'], abi)
                    )
                    
                    logger.info(f"Initialized {dex_name} pool contract for {pair_name}")
            
        except Exception as e:
            logger.error(f"Error initializing DEX contracts: {e}")
            raise
    
    def get_uniswap_v3_price(self, pair_name: str) -> Optional[Decimal]:
        """Get price from UniswapV3 pool using QuoterV2"""
        @self.web3_manager.with_retry
        def _get_price() -> Optional[Decimal]:
            try:
                pool_info = self.dex_config['dexes']['uniswap_v3']['pools'][pair_name]
                token0 = pool_info['token0']
                token1 = pool_info['token1']
                fee = pool_info['fee']
                
                # Get token decimals
                token0_decimals = self.dex_config['tokens'][pool_info['token0_symbol']]['decimals']
                token1_decimals = self.dex_config['tokens'][pool_info['token1_symbol']]['decimals']
                
                # Use 1 token0 as input amount
                amount_in = 10 ** token0_decimals
                
                try:
                    # Use QuoterV2 for price quote
                    quote = self.uniswap_quoter.functions.quoteExactInputSingle((
                        token0,          # tokenIn
                        token1,          # tokenOut
                        amount_in,       # amountIn
                        fee,            # fee
                        0               # sqrtPriceLimitX96 (0 for no limit)
                    )).call()
                    
                    # QuoterV2 returns a tuple with amountOut and other data
                    amount_out = quote[0]
                    
                    # Calculate price accounting for decimals
                    price = Decimal(amount_out) / Decimal(10**token1_decimals)
                    logger.info(f"Calculated price for {pair_name}: {price}")
                    return price
                    
                except Exception as e:
                    logger.error(f"Error calling quoter for {pair_name}: {e}")
                    return None
                
            except Exception as e:
                logger.error(f"Error getting UniswapV3 price for {pair_name}: {str(e)}")
                return None
        
        return _get_price()
    
    def get_aerodrome_price(self, pair_name: str) -> Optional[Decimal]:
        """Get price from Aerodrome pool using metadata"""
        @self.web3_manager.with_retry
        def _get_price() -> Optional[Decimal]:
            try:
                if pair_name not in self.contracts['aerodrome']:
                    logger.error(f"Pool contract not found for {pair_name}")
                    return None
                    
                pool = self.contracts['aerodrome'][pair_name]
                logger.info(f"Getting price for {pair_name} from pool {pool.address}")
                
                # Get pool metadata which includes reserves and decimals
                try:
                    metadata = pool.functions.metadata().call()
                    dec0, dec1, r0, r1, is_stable, t0, t1 = metadata
                    
                    if r0 == 0 or r1 == 0:
                        logger.warning(f"Zero reserves in pool for {pair_name}")
                        return None
                    
                    # Calculate price accounting for decimals
                    # For stable pools, we use the raw ratio as they're meant to be pegged
                    # For volatile pools, we adjust by decimals
                    if is_stable:
                        price = Decimal(r1) / Decimal(r0)
                    else:
                        decimal_adjustment = Decimal(10 ** (dec1 - dec0))
                        price = (Decimal(r1) / Decimal(r0)) * decimal_adjustment
                    
                    logger.info(f"Calculated price for {pair_name}: {price}")
                    return price
                    
                except Exception as e:
                    # If metadata call fails, try fallback to getReserves
                    logger.warning(f"Metadata call failed, trying getReserves: {e}")
                    reserves = pool.functions.getReserves().call()
                    reserve0, reserve1, _ = reserves
                    
                    # Get token decimals from config
                    pool_info = self.dex_config['dexes']['aerodrome']['pools'][pair_name]
                    token0 = pool_info['token0']
                    token1 = pool_info['token1']
                    
                    # Find token info in the tokens section
                    token0_info = next((info for symbol, info in self.dex_config['tokens'].items() 
                                      if info['address'].lower() == token0.lower()), None)
                    token1_info = next((info for symbol, info in self.dex_config['tokens'].items() 
                                      if info['address'].lower() == token1.lower()), None)
                    
                    if not token0_info or not token1_info:
                        logger.error(f"Could not find token info for {pair_name}")
                        return None
                    
                    token0_decimals = token0_info['decimals']
                    token1_decimals = token1_info['decimals']
                    
                    # Calculate price accounting for decimals
                    decimal_adjustment = Decimal(10 ** (token1_decimals - token0_decimals))
                    price = Decimal(reserve1) / Decimal(reserve0) * decimal_adjustment
                    
                    logger.info(f"Calculated price for {pair_name}: {price}")
                    return price
                
            except Exception as e:
                logger.error(f"Error getting Aerodrome price for {pair_name}: {str(e)}")
                return None
        
        return _get_price()
    
    def get_price(self, dex_name: str, pair_name: str) -> Optional[Decimal]:
        """Get price from specified DEX"""
        try:
            if dex_name == 'uniswap_v3':
                return self.get_uniswap_v3_price(pair_name)
            elif dex_name == 'aerodrome':
                return self.get_aerodrome_price(pair_name)
            else:
                logger.error(f"Unsupported DEX: {dex_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting price from {dex_name} for {pair_name}: {e}")
            return None
    
    def get_all_prices(self) -> Dict[str, Dict[str, Optional[Decimal]]]:
        """Get prices from all configured DEXes"""
        prices = {}
        
        for dex_name in self.dex_config['dexes']:
            prices[dex_name] = {}
            for pair_name in self.dex_config['dexes'][dex_name]['pools']:
                # Skip pairs without pool addresses for UniswapV3
                if (dex_name == 'uniswap_v3' and 
                    'address' not in self.dex_config['dexes'][dex_name]['pools'][pair_name]):
                    continue
                prices[dex_name][pair_name] = self.get_price(dex_name, pair_name)
        
        return prices
    
    def calculate_price_difference(
        self,
        pair_name: str,
        base_dex: str = 'uniswap_v3',
        quote_dex: str = 'aerodrome'
    ) -> Optional[Tuple[Decimal, Decimal, Decimal]]:
        """Calculate price difference between two DEXes"""
        try:
            base_price = self.get_price(base_dex, pair_name)
            quote_price = self.get_price(quote_dex, pair_name)
            
            if base_price is None or quote_price is None:
                return None
            
            price_diff = quote_price - base_price
            price_diff_percent = (price_diff / base_price) * Decimal('100')
            
            return (base_price, quote_price, price_diff_percent)
            
        except Exception as e:
            logger.error(
                f"Error calculating price difference for {pair_name} "
                f"between {base_dex} and {quote_dex}: {e}"
            )
            return None
    
    def check_arbitrage_opportunities(self) -> Dict[str, Dict[str, Any]]:
        """Check for arbitrage opportunities across all pairs"""
        opportunities = {}
        
        for pair in self.dex_config['pairs']:
            pair_name = pair['name']
            min_profit = Decimal(pair['min_profit_threshold'])
            
            price_info = self.calculate_price_difference(pair_name)
            if price_info:
                base_price, quote_price, price_diff_percent = price_info
                
                if abs(price_diff_percent) > min_profit:
                    opportunities[pair_name] = {
                        'base_price': float(base_price),
                        'quote_price': float(quote_price),
                        'price_difference_percent': float(price_diff_percent),
                        'profitable': True,
                        'direction': 'buy' if quote_price > base_price else 'sell'
                    }
        
        return opportunities

def get_dex_interface() -> DexInterface:
    """Get or create DexInterface instance"""
    return DexInterface()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        dex = get_dex_interface()
        prices = dex.get_all_prices()
        
        logger.info("Current prices:")
        for dex_name, dex_prices in prices.items():
            for pair_name, price in dex_prices.items():
                if price is not None:
                    logger.info(f"{dex_name} - {pair_name}: {float(price)}")
        
        opportunities = dex.check_arbitrage_opportunities()
        if opportunities:
            logger.info("\nArbitrage opportunities found:")
            for pair, opp in opportunities.items():
                logger.info(f"{pair}: {opp}")
        else:
            logger.info("\nNo arbitrage opportunities found")
            
    except Exception as e:
        logger.error(f"Error in price monitoring: {e}")
