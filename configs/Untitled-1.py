"""Trading strategies implementation focusing on BaseSwap with enhanced price analysis"""

from typing import List, Dict, Any, Optional, Union, Literal, cast, TypedDict, TypeVar
from enum import Enum
import logging
import sys
from web3 import Web3
from web3.contract import Contract
import json
import os
from decimal import Decimal
from .price_normalizer import validate_normalized_price
from .ml_strategy import MLOpportunityScorer
from .price_analysis import PriceAnalyzer

NetworkNameType = Literal['ethereum', 'binance_smart_chain', 'polygon', 'base']

T = TypeVar('T', bound='AbiDict')

class AbiDict(TypedDict):
    inputs: List[Dict[str, Any]]
    outputs: Optional[List[Dict[str, Any]]]
    stateMutability: str
    type: str
    name: Optional[str]

class OpportunityDict(TypedDict):
    token_in: str
    token_out: str
    dex_a_price: float
    dex_b_price: float
    spread_percent: float
    direction: str
    ml_score: float

class NetworkName(Enum):
    ETHEREUM = 'ethereum'
    BINANCE_SMART_CHAIN = 'binance_smart_chain'
    POLYGON = 'polygon'
    BASE = 'base'

    @classmethod
    def from_str(cls, network_str: str) -> 'NetworkName':
        try:
            return cls(network_str.lower())
        except ValueError:
            raise ValueError(f"Invalid network name: {network_str}")

    def capitalize(self) -> str:
        return self.value.capitalize()

def load_abi(filename: str) -> List[AbiDict]:
    try:
        path = os.path.join('abi', filename)
        with open(path, 'r') as f:
            data = json.load(f)
            return cast(List[AbiDict], data)
    except Exception as e:
        logging.error(f"Error loading ABI {filename}: {e}")
        return []

def get_web3_client(network: NetworkNameType) -> Optional[Web3]:
    try:
        from configs.performance_optimized_loader import get_rpc_endpoint
        network_cast = cast(NetworkNameType, network)
        endpoint = get_rpc_endpoint(network_cast)
        return Web3(Web3.HTTPProvider(endpoint)) if endpoint else None
    except ImportError:
        return None

class TradingStrategy:
    def __init__(self, network: NetworkName):
        self.network = network
        self.web3_client = get_web3_client(cast(NetworkNameType, network.value))
        self.logger = logging.getLogger(f'{self.__class__.__name__}_{network.value}')
    
    def validate_network(self) -> bool:
        if not self.web3_client:
            return False
        try:
            return self.web3_client.is_connected()
        except Exception:
            return False
    
    def get_network_params(self) -> Dict[str, Any]:
        if not self.web3_client:
            return {}
        try:
            return {
                'network': self.network.value,
                'block_number': self.web3_client.eth.block_number,
                'gas_price': self.web3_client.eth.gas_price
            }
        except Exception:
            return {}

class ArbitrageStrategy(TradingStrategy):
    def __init__(self, network: NetworkName, exchanges: List[str]):
        super().__init__(network)
        self.exchanges = exchanges
        self.router_contracts: Dict[str, Contract] = {}
        self.token_contracts: Dict[str, Contract] = {}
        self.token_decimals: Dict[str, int] = {}
        self.ml_scorer = MLOpportunityScorer()
        self.price_analyzer = PriceAnalyzer()
        if self.web3_client:
            self._initialize_contracts()
    
    def _initialize_contracts(self) -> None:
        try:
            if not self.web3_client:
                return

            router_abi = load_abi('IUniswapV2Router.json')
            erc20_abi = load_abi('ERC20.json')
            
            if not router_abi or not erc20_abi:
                self.logger.error("Failed to load ABIs")
                return
            
            dex_configs = {
                'baseswap': {
                    'address': '0x327Df1E6de05895d2ab08513aaDD9313Fe505d86',
                    'abi': router_abi
                }
            }
            
            token_addresses = {
                'WETH': '0x4200000000000000000000000000000000000006',
                'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
                'DAI': '0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb'
            }
            
            for dex, config in dex_configs.items():
                if dex in self.exchanges:
                    self.logger.info(f"Initializing {dex} router at {config['address']}")
                    self.router_contracts[dex] = self.web3_client.eth.contract(
                        address=self.web3_client.to_checksum_address(config['address']),
                        abi=config['abi']
                    )
            
            for token, address in token_addresses.items():
                self.logger.info(f"Initializing {token} token at {address}")
                token_contract = self.web3_client.eth.contract(
                    address=self.web3_client.to_checksum_address(address),
                    abi=erc20_abi
                )
                self.token_contracts[token] = token_contract
                try:
                    self.token_decimals[token] = token_contract.functions.decimals().call()
                    self.logger.info(f"{token} decimals: {self.token_decimals[token]}")
                except Exception as e:
                    self.logger.error(f"Error getting decimals for {token}: {e}")
                    self.token_decimals[token] = 18
                
        except Exception as e:
            self.logger.error(f"Error initializing contracts: {e}")

    def get_token_price(self, dex: str, token_in: str, token_out: str) -> Optional[Decimal]:
        try:
            if not self.web3_client or dex not in self.router_contracts:
                return None

            if token_in not in self.token_contracts or token_out not in self.token_contracts:
                return None
                
            token_in_addr = self.token_contracts[token_in].address
            token_out_addr = self.token_contracts[token_out].address
            
            self.logger.info(f"Getting price from {dex} for {token_in}/{token_out}")
            
            decimals_in = self.token_decimals.get(token_in, 18)
            decimals_out = self.token_decimals.get(token_out, 18)
            base_amount = 10 ** decimals_in

            router = self.router_contracts[dex]
            try:
                amounts_out = router.functions.getAmountsOut(
                    base_amount,
                    [token_in_addr, token_out_addr]
                ).call()
                
                if len(amounts_out) < 2 or amounts_out[0] == 0:
                    self.logger.warning(f"Invalid amounts from {dex}: {amounts_out}")
                    return None
                
                amount_in_dec = Decimal(amounts_out[0]) / Decimal(10 ** decimals_in)
                amount_out_dec = Decimal(amounts_out[1]) / Decimal(10 ** decimals_out)
                price = amount_out_dec / amount_in_dec

                self.logger.info(f"Raw price from {dex}: {price} {token_out} per {token_in}")
                
                if not validate_normalized_price(price, min_price=Decimal('0.0003'), max_price=Decimal('3500')):
                    return None

                # Record price in database
                token_pair = f"{token_in}/{token_out}"
                self.price_analyzer.add_price_record(
                    token_pair=token_pair,
                    exchange=dex,
                    price=float(price),
                    block_number=self.web3_client.eth.block_number
                )

                self.logger.info(f"Final price from {dex}: {price}")
                return price
                    
            except Exception as e:
                self.logger.warning(f"Failed to get price from {dex} for {token_in}/{token_out}: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in get_token_price: {e}")
            return None

    def find_arbitrage_opportunities(self) -> List[OpportunityDict]:
        opportunities: List[OpportunityDict] = []
        token_pairs = [
            ('WETH', 'USDC'),
            ('WETH', 'DAI'),
            ('USDC', 'DAI')
        ]
        
        for token_in, token_out in token_pairs:
            prices: Dict[str, Optional[Decimal]] = {}
            for dex in self.exchanges:
                price = self.get_token_price(dex, token_in, token_out)
                if price is not None:
                    prices[dex] = price
                else:
                    self.logger.warning(f"Price not available from {dex} for {token_in}/{token_out}")
            
            if len(prices) < 2:
                continue
            
            dex_list = list(prices.keys())
            for i in range(len(dex_list)):
                for j in range(i + 1, len(dex_list)):
                    dex_a = dex_list[i]
                    dex_b = dex_list[j]
                    price_a = prices[dex_a]
                    price_b = prices[dex_b]
                    
                    if price_a and price_b:
                        price_diff = abs(price_a - price_b)
                        avg_price = (price_a + price_b) / 2
                        spread_percent = (price_diff / avg_price) * 100
                        
                        if spread_percent > 0.5:
                            # Get price statistics for volatility calculation
                            token_pair = f"{token_in}/{token_out}"
                            stats_a = self.price_analyzer.get_price_statistics(token_pair, dex_a)
                            stats_b = self.price_analyzer.get_price_statistics(token_pair, dex_b)
                            
                            # Calculate average volatility
                            volatility = (
                                (stats_a['volatility'] if stats_a else 0) +
                                (stats_b['volatility'] if stats_b else 0)
                            ) / 2 if stats_a or stats_b else 0
                            
                            # Estimate potential profit (simplified)
                            amount_in_usd = 1000  # $1000 trade size
                            potential_profit_usd = float(amount_in_usd * (spread_percent / 100))
                            gas_cost_usd = float(5)  # Estimated gas cost in USD
                            net_profit_usd = potential_profit_usd - gas_cost_usd
                            
                            # Record opportunity
                            self.price_analyzer.add_opportunity(
                                token_pair=token_pair,
                                exchange_in=dex_a,
                                exchange_out=dex_b,
                                price_in=float(price_a),
                                price_out=float(price_b),
                                spread_percent=float(spread_percent),
                                potential_profit_usd=potential_profit_usd,
                                gas_cost_usd=gas_cost_usd,
                                net_profit_usd=net_profit_usd
                            )
                            
                            opportunity: OpportunityDict = {
                                'token_in': token_in,
                                'token_out': token_out,
                                'dex_a_price': float(price_a),
                                'dex_b_price': float(price_b),
                                'spread_percent': float(spread_percent),
                                'direction': f'{dex_a}_to_{dex_b}' if price_a < price_b else f'{dex_b}_to_{dex_a}',
                                'ml_score': 0.0
                            }
                            
                            # Calculate opportunity score using price analysis
                            opportunity['ml_score'] = self.price_analyzer.calculate_opportunity_score(
                                spread_percent=float(spread_percent),
                                volatility=volatility,
                                net_profit_usd=net_profit_usd
                            )
                            
                            opportunities.append(opportunity)
                            
        return sorted(opportunities, key=lambda x: x['ml_score'], reverse=True)

class TradingStrategyManager:
    def __init__(self, networks: Union[List[NetworkName], List[str]]):
        self.networks = [
            network if isinstance(network, NetworkName) 
            else NetworkName.from_str(network) 
            for network in networks
        ]
        
        self.strategies: List[ArbitrageStrategy] = []
        self.logger = logging.getLogger('TradingStrategyManager')
        
        for network in self.networks:
            strategy = ArbitrageStrategy(
                network=network, 
                exchanges=['baseswap'] if network == NetworkName.BASE  # Only using BaseSwap for now
                else ['uniswap', 'sushiswap']
            )
            self.strategies.append(strategy)
    
    def start_strategies(self) -> None:
        self.logger.info("Starting trading strategies...")
        for strategy in self.strategies:
            if strategy.validate_network():
                self.logger.info(f"Strategy for {strategy.network.value} validated")
                opportunities = strategy.find_arbitrage_opportunities()
                if opportunities:
                    self.logger.info(f"Found opportunities: {opportunities}")
                else:
                    self.logger.info("No arbitrage opportunities found")
            else:
                self.logger.warning(f"Strategy for {strategy.network.value} failed network validation")
    
    def stop_strategies(self) -> None:
        self.logger.info("Stopping trading strategies...")

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    strategy_manager = TradingStrategyManager(['base'])
    strategy_manager.start_strategies()

if __name__ == "__main__":
    main()
