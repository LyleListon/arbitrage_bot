from web3 import Web3
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseDEXInteraction(ABC):
    """Base class for DEX interactions"""
    def __init__(self, web3: Web3, router_address: str, abi_path: str):
        self.web3 = web3
        with open(abi_path, 'r') as abi_file:
            router_abi = json.load(abi_file)
        self.router_contract = self.web3.eth.contract(address=router_address, abi=router_abi)

    @abstractmethod
    def get_amounts_out(self, amount_in: int, path: list) -> list:
        """Get expected output amounts for a given input amount and path"""
        pass

    @abstractmethod
    def swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int):
        """Execute a token swap"""
        pass

    def check_liquidity(self, token_in: str, token_out: str, amount_in: int) -> Dict:
        """Check liquidity depth for a given pair and amount"""
        try:
            # Get price impact for different percentages of the input amount
            impacts = []
            percentages = [0.2, 0.4, 0.6, 0.8, 1.0]
            
            base_amount = amount_in // len(percentages)
            for pct in percentages:
                test_amount = int(base_amount * pct)
                if test_amount > 0:
                    try:
                        amounts = self.get_amounts_out(test_amount, [token_in, token_out])
                        rate = amounts[-1] / test_amount
                        impacts.append({
                            'percentage': pct * 100,
                            'amount_in': test_amount,
                            'amount_out': amounts[-1],
                            'rate': rate
                        })
                    except Exception as e:
                        logger.error(f"Error checking impact at {pct * 100}%: {str(e)}")
                        break

            if not impacts:
                return {'status': 'error', 'message': 'No liquidity data available'}

            # Calculate price impact
            base_rate = impacts[0]['rate']
            max_impact = 0
            for impact in impacts:
                current_impact = abs((impact['rate'] - base_rate) / base_rate) * 100
                max_impact = max(max_impact, current_impact)

            return {
                'status': 'success',
                'max_impact': max_impact,
                'base_rate': base_rate,
                'impacts': impacts,
                'sufficient_liquidity': max_impact < 5  # Consider <5% impact as sufficient
            }

        except Exception as e:
            logger.error(f"Error checking liquidity: {str(e)}")
            return {'status': 'error', 'message': str(e)}


class UniswapV2Interaction(BaseDEXInteraction):
    """Uniswap V2 interaction implementation"""
    def __init__(self, web3: Web3, router_address: str):
        super().__init__(web3, router_address, 'abi/uniswap_v2_router.json')

    def get_amounts_out(self, amount_in: int, path: list) -> list:
        return self.router_contract.functions.getAmountsOut(amount_in, path).call()

    def swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int):
        return self.router_contract.functions.swapExactTokensForTokens(
            amount_in,
            amount_out_min,
            path,
            to,
            deadline
        )


class UniswapV3Interaction(BaseDEXInteraction):
    """Uniswap V3 interaction implementation"""
    def __init__(self, web3: Web3, router_address: str):
        super().__init__(web3, router_address, 'abi/uniswap_v3_router.json')

    def get_amounts_out(self, amount_in: int, path: list) -> list:
        # V3 uses different method for quotes
        return self.router_contract.functions.quoteExactInputSingle(
            path[0],  # tokenIn
            path[-1],  # tokenOut
            3000,     # fee tier (default to 0.3%)
            amount_in,
            0         # sqrtPriceLimitX96
        ).call()

    def swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int):
        return self.router_contract.functions.exactInputSingle({
            'tokenIn': path[0],
            'tokenOut': path[-1],
            'fee': 3000,
            'recipient': to,
            'deadline': deadline,
            'amountIn': amount_in,
            'amountOutMinimum': amount_out_min,
            'sqrtPriceLimitX96': 0
        })


class SushiswapInteraction(UniswapV2Interaction):
    """Sushiswap interaction implementation (uses Uniswap V2 interface)"""
    def __init__(self, web3: Web3, router_address: str):
        super().__init__(web3, router_address)


class PancakeswapInteraction(UniswapV2Interaction):
    """Pancakeswap interaction implementation (uses Uniswap V2 interface)"""
    def __init__(self, web3: Web3, router_address: str):
        super().__init__(web3, router_address)


class CurveInteraction(BaseDEXInteraction):
    """Curve interaction implementation"""
    def __init__(self, web3: Web3, router_address: str):
        super().__init__(web3, router_address, 'abi/curve_pool.json')

    def get_amounts_out(self, amount_in: int, path: list) -> list:
        # Curve uses different method for quotes
        return self.router_contract.functions.get_dy(
            0,  # i (index of input token)
            1,  # j (index of output token)
            amount_in
        ).call()

    def swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int):
        return self.router_contract.functions.exchange(
            0,  # i (index of input token)
            1,  # j (index of output token)
            amount_in,
            amount_out_min
        )


class BalancerInteraction(BaseDEXInteraction):
    """Balancer interaction implementation with pool ID lookup and liquidity analysis"""
    def __init__(self, web3: Web3, router_address: str):
        super().__init__(web3, router_address, 'abi/balancer_vault.json')
        
        # Initialize pool registry contract
        with open('abi/balancer_pool_registry.json', 'r') as f:
            registry_abi = json.load(f)
        self.registry_contract = web3.eth.contract(
            address=router_address,  # Vault address is also registry address
            abi=registry_abi
        )
        
        # Initialize cache
        self.pool_id_cache: Dict[Tuple[str, str], Dict] = {}
        self.cache_expiry = 300  # 5 minutes cache expiry

    def _get_pool_id(self, token_in: str, token_out: str) -> str:
        """Get pool ID for given token pair with caching and liquidity checks"""
        cache_key = (token_in, token_out)
        
        # Check cache
        if cache_key in self.pool_id_cache:
            cache_entry = self.pool_id_cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self.cache_expiry:
                return cache_entry['pool_id']
        
        try:
            # Get all pools containing both tokens
            pool_ids = self.registry_contract.functions.getPoolsWithTokens(
                [token_in, token_out]
            ).call()
            
            if not pool_ids:
                raise ValueError(f"No Balancer pool found for {token_in} - {token_out}")
            
            # Find pool with best liquidity
            best_pool = None
            max_liquidity = 0
            
            for pool_id in pool_ids:
                try:
                    # Get pool tokens and balances
                    tokens, balances, _ = self.registry_contract.functions.getPoolTokens(
                        pool_id
                    ).call()
                    
                    # Find indices of our tokens
                    token_in_idx = tokens.index(token_in)
                    token_out_idx = tokens.index(token_out)
                    
                    # Use minimum balance as liquidity indicator
                    liquidity = min(balances[token_in_idx], balances[token_out_idx])
                    
                    if liquidity > max_liquidity:
                        max_liquidity = liquidity
                        best_pool = pool_id
                        
                except Exception as e:
                    logger.error(f"Error checking pool {pool_id}: {str(e)}")
                    continue
            
            if not best_pool:
                raise ValueError("No viable pool found")
            
            # Cache the result
            self.pool_id_cache[cache_key] = {
                'pool_id': best_pool,
                'timestamp': time.time(),
                'liquidity': max_liquidity
            }
            
            return best_pool
            
        except Exception as e:
            logger.error(f"Error in pool ID lookup: {str(e)}")
            raise

    def get_amounts_out(self, amount_in: int, path: list) -> list:
        """Get expected output amounts for Balancer swap"""
        pool_id = self._get_pool_id(path[0], path[1])
        
        # Query swap outcome
        result = self.router_contract.functions.queryBatchSwap(
            0,  # kind (0 for given in)
            [{
                'poolId': pool_id,
                'assetIn': path[0],
                'assetOut': path[1],
                'amount': amount_in
            }],
            path[0],  # tokenIn
            path[1]   # tokenOut
        ).call()
        
        return [amount_in, abs(result[1])]  # Return as [amountIn, amountOut]

    def swap_exact_tokens_for_tokens(self, amount_in: int, amount_out_min: int, path: list, to: str, deadline: int):
        """Execute a Balancer swap with gas optimization"""
        pool_id = self._get_pool_id(path[0], path[1])
        
        # Check liquidity before swap
        liquidity_info = self.check_liquidity(path[0], path[1], amount_in)
        if liquidity_info['status'] == 'success' and not liquidity_info['sufficient_liquidity']:
            raise ValueError(f"Insufficient liquidity. Price impact: {liquidity_info['max_impact']}%")
        
        # Build optimized swap parameters
        return self.router_contract.functions.swap(
            {
                'kind': 0,  # 0 for exact input
                'assets': path,
                'limits': [amount_in, amount_out_min],
                'deadline': deadline,
                'recipient': to
            },
            [{'poolId': pool_id, 'amount': amount_in}],
            amount_out_min
        )


def is_valid_address(address: str) -> bool:
    """Validate Ethereum address format"""
    return Web3.is_address(address)


def create_dex_interaction(web3: Web3, dex_name: str, router_address: str) -> Optional[BaseDEXInteraction]:
    """Factory function to create appropriate DEX interaction instance"""
    if not is_valid_address(router_address):
        logger.warning(f"Invalid router address for {dex_name}: {router_address}")
        return None
    
    dex_classes = {
        'uniswapv2': UniswapV2Interaction,
        'uniswapv3': UniswapV3Interaction,
        'sushiswap': SushiswapInteraction,
        'pancakeswap': PancakeswapInteraction,
        'curve': CurveInteraction,
        'balancer': BalancerInteraction
    }
    
    dex_class = dex_classes.get(dex_name.lower())
    if dex_class:
        try:
            return dex_class(web3, router_address)
        except Exception as e:
            logger.error(f"Error creating {dex_name} interaction: {str(e)}")
            return None
    else:
        logger.error(f"Unsupported DEX: {dex_name}")
        return None
