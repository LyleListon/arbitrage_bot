import os
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env file

def load_config():
    return {
        'networks': {
            'mainnet': {
                'rpc_url': os.getenv('MAINNET_RPC_URL'),
                'chain_id': 1
            },
            'holesky': {
                'rpc_url': os.getenv('HOLESKY_RPC_URL'),
                'chain_id': 17000
            },
            'binance_smart_chain': {
                'rpc_url': os.getenv('BSC_RPC_URL'),
                'chain_id': 97
            }
        },
        'tokens': [
            os.getenv('TOKEN_1_ADDRESS'),
            os.getenv('TOKEN_2_ADDRESS'),
            os.getenv('TOKEN_3_ADDRESS')
        ],
        'dexes': {
            'uniswap': {
                'mainnet': {'router': os.getenv('UNISWAP_MAINNET_ROUTER'), 'type': 1},
                'holesky': {'router': os.getenv('UNISWAP_HOLESKY_ROUTER'), 'type': 1}
            },
            'pancakeswap': {
                'binance_smart_chain': {'router': os.getenv('PANCAKESWAP_BSC_ROUTER'), 'type': 1}
            }
        },
        'arbitrage_paths': [
            [os.getenv('TOKEN_1_ADDRESS'), os.getenv('TOKEN_2_ADDRESS')],
            [os.getenv('TOKEN_1_ADDRESS'), os.getenv('TOKEN_2_ADDRESS'), os.getenv('TOKEN_3_ADDRESS')]
        ],
        'dex_sequences': [
            ['uniswap', 'pancakeswap'],
            ['uniswap', 'uniswap', 'uniswap']
        ],
        'flash_loan': {
            'enabled': True,
            'min_amount': 10000000000000000000,  # 10 ETH in wei
            'max_amount': 1000000000000000000000,  # 1000 ETH in wei
            'contract_address': os.getenv('FLASH_LOAN_CONTRACT'),
            'fee_percentage': 0.0009,  # 0.09% fee
            'supported_tokens': [
                os.getenv('FLASH_LOAN_TOKEN_1'),
                os.getenv('FLASH_LOAN_TOKEN_2')
            ],
            'gas_overhead': 100000  # Estimated additional gas cost for flash loan
        },
        'security': {
            'min_profit_threshold': 0.001,
            'max_slippage': 0.005,
            'max_trade_size': 100000000000000000000,  # 100 ETH in wei
            'max_gas_price': 300,  # in gwei
            'min_liquidity_ratio': 2  # Minimum ratio of liquidity to trade size
        },
        'gas': {
            'mainnet': {
                'max_price_gwei': 100,
                'priority_fee_gwei': 2
            },
            'holesky': {
                'max_price_gwei': 50,
                'priority_fee_gwei': 1
            }
        },
        'execution': {
            'timeout': 120,
            'cool_down_period': 30,
            'check_interval': 60,
            'max_concurrent_trades': 3,
            'max_retries': 3,
            'retry_delay': 5  # in seconds
        },
        'monitoring': {
            'min_success_rate': 0.8,
            'min_daily_profit': 0.1,  # In ETH
            'profit_window': 86400,  # 24 hours in seconds
            'max_gas_cost_ratio': 0.1,  # Maximum ratio of gas cost to profit
            'health_check': {
                'max_block_delay': 60,
                'max_pending_tx': 1000,
                'min_peer_count': 3
            },
            'alerts': {
                'enabled': os.getenv('ENABLE_ALERTS', 'False').lower() == 'true',
                'email': os.getenv('ALERT_EMAIL'),
                'cooldown': 300,
                'max_daily_alerts': 10,
                'smtp_server': os.getenv('SMTP_SERVER'),
                'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                'username': os.getenv('SMTP_USERNAME'),
                'password': os.getenv('SMTP_PASSWORD'),
                'sender': os.getenv('ALERT_SENDER'),
                'recipient': os.getenv('ALERT_RECIPIENT')
            }
        },
        'logging': {
            'file': 'arbitrage_bot.log',
            'level': 'INFO'
        },
        'wallet_address': os.getenv('WALLET_ADDRESS'),
        'contracts': {
            'arbitrage_bot': os.getenv('ARBITRAGE_BOT_CONTRACT'),
            'price_feed': os.getenv('PRICE_FEED_CONTRACT')
        }
    }
