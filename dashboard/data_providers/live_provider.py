import logging
from web3 import Web3
from typing import Dict, Optional, Any
import time
import json
from decimal import Decimal

logger = logging.getLogger(__name__)


class PriceValidationError(Exception):
    """Raised when price validation fails"""
    pass


class LiveDataProvider:
    def __init__(self, web3: Web3, config: dict) -> None:
        self.web3 = web3
        self.config = config
        self.price_cache: Dict[str, int] = {}
        self.cache_timeout = 30  # 30 seconds
        self.last_update: Dict[str, float] = {}

        # Load UniswapV3 Quoter ABI
        with open('abi/IUniswapV3QuoterV2.json', 'r') as f:
            self.quoter_abi = json.load(f)

        # Initialize Uniswap V3 contracts
        if 'exchanges' in config and 'uniswap_v3' in config['exchanges']:
            self.quoter = self.web3.eth.contract(
                address=Web3.to_checksum_address(config['exchanges']['uniswap_v3']['quoter']),
                abi=self.quoter_abi
            )
            logger.info("Initialized Uniswap V3 contracts")
        else:
            logger.error("Missing Uniswap V3 configuration")
            raise ValueError("Missing Uniswap V3 configuration")

    def get_v3_quote(self, token_in: str, token_out: str, amount_in: int) -> Optional[int]:
        """Get quote from Uniswap V3"""
        try:
            # Get fee tiers from config
            fee_tiers = self.config['exchanges']['uniswap_v3']['fee_tiers']
            best_quote = 0

            for fee_tier in fee_tiers:
                try:
                    params = {
                        'tokenIn': Web3.to_checksum_address(token_in),
                        'tokenOut': Web3.to_checksum_address(token_out),
                        'amountIn': amount_in,
                        'fee': fee_tier,
                        'sqrtPriceLimitX96': 0
                    }

                    quote = self.quoter.functions.quoteExactInputSingle(params).call()

                    if quote > best_quote:
                        best_quote = quote

                except Exception as e:
                    logger.debug(f"Failed to get quote for fee tier {fee_tier}: {str(e)}")
                    continue

            return best_quote if best_quote > 0 else None

        except Exception as e:
            logger.debug(f"Failed to get V3 quote: {str(e)}")
            return None

    def get_price(self, token_in: str, token_out: str, amount_in: int) -> Optional[int]:
        """Get the best price for a token pair"""
        cache_key = f"{token_in}-{token_out}-{amount_in}"

        # Check cache
        if cache_key in self.price_cache:
            last_update = self.last_update.get(cache_key, 0)
            if time.time() - last_update < self.cache_timeout:
                return self.price_cache[cache_key]

        # Get V3 quote
        amount_out = self.get_v3_quote(token_in, token_out, amount_in)

        if amount_out and amount_out > 0:
            # Validate price before caching
            if self._validate_price(token_in, token_out, amount_in, amount_out):
                self.price_cache[cache_key] = amount_out
                self.last_update[cache_key] = time.time()
                return amount_out
            else:
                raise PriceValidationError(f"Price validation failed for {token_in}/{token_out}")

        return None

    def _validate_price(self, token_in: str, token_out: str, amount_in: int, amount_out: int) -> bool:
        """Validate price against configured thresholds"""
        try:
            # Get token pair config
            pair_key = None
            for pair_name, pair_config in self.config['pairs'].items():
                if (pair_config['base_token'].lower() == token_in.lower() and
                    pair_config['quote_token'].lower() == token_out.lower()):
                    pair_key = pair_name
                    break

            if not pair_key:
                logger.warning(f"No configuration found for pair {token_in}/{token_out}")
                return False

            pair_config = self.config['pairs'][pair_key]

            # Calculate price impact
            price_impact = abs(1 - (Decimal(amount_out) / Decimal(amount_in)))

            # Check against max slippage
            if price_impact > Decimal(pair_config['max_slippage']):
                logger.warning(f"Price impact {price_impact} exceeds max slippage {pair_config['max_slippage']}")
                return False

            return True

        except Exception as e:
            logger.error(f"Price validation error: {str(e)}")
            return False

    def get_all_prices(self) -> Dict[str, int]:
        """Get all configured token pair prices"""
        prices = {}

        for pair_name, pair_config in self.config['pairs'].items():
            if pair_config['is_active']:
                base_token = pair_config['base_token']
                quote_token = pair_config['quote_token']
                amount_in = Web3.to_wei(1, 'ether')  # 1 token

                try:
                    price = self.get_price(base_token, quote_token, amount_in)
                    if price:
                        prices[pair_name] = price
                except PriceValidationError:
                    logger.warning(f"Price validation failed for {pair_name}")
                    continue

        return prices

    def clear_cache(self) -> None:
        """Clear the price cache"""
        self.price_cache.clear()
        self.last_update.clear()
