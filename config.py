"""
Enhanced configuration for arbitrage bot with security and monitoring
"""
from web3 import Web3
import os
from dotenv import load_dotenv


def load_config():
    """Load configuration with security and monitoring parameters"""
    # Load appropriate environment file
    network = os.getenv('DEPLOY_NETWORK', 'mainnet')
    load_dotenv(f'.env.{network}')

    return {
        'networks': {
            'mainnet': {
                'rpc_url': os.getenv('MAINNET_RPC_URL'),
                'chain_id': 1,
                'explorer': 'https://etherscan.io',
                'block_time': 12,  # seconds
                'required_confirmations': 2
            },
            'holesky': {
                'rpc_url': os.getenv('HOLESKY_RPC_URL'),
                'chain_id': 17000,
                'explorer': 'https://holesky.etherscan.io',
                'block_time': 12,
                'required_confirmations': 1
            },
        },
        'tokens': {
            'mainnet': {
                'weth': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'usdc': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
                'usdt': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                'dai': '0x6B175474E89094C44Da98b954EedeAC495271d0F'
            },
        },
        'dexes': {
            'uniswap_v2': {
                'mainnet': {
                    'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                    'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
                    'fee': 0.003,
                    'min_liquidity': Web3.to_wei(50, 'ether'),  # Minimum pool liquidity
                    'max_price_impact': 0.01  # Maximum price impact (1%)
                },
            },
            'sushiswap': {
                'mainnet': {
                    'router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
                    'factory': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
                    'fee': 0.003,
                    'min_liquidity': Web3.to_wei(50, 'ether'),
                    'max_price_impact': 0.01
                },
            },
        },
        'gas': {
            'mainnet': {
                'max_price_gwei': int(os.getenv('MAX_GAS_PRICE_GWEI', '100')),
                'priority_fee_gwei': 2,
                'base_fee_multiplier': 1.2,  # Multiply base fee by this for faster inclusion
                'max_base_fee_gwei': 80,  # Maximum acceptable base fee
                'min_base_fee_gwei': 10,  # Minimum base fee to ensure transaction doesn't stick
                'estimate_buffer': 1.2  # Buffer for gas estimation
            },
        },
        'security': {
            'max_slippage': float(os.getenv('MAX_SLIPPAGE', '0.005')),  # 0.5%
            'min_profit_threshold': float(os.getenv('MIN_PROFIT_THRESHOLD', '0.02')),  # 2%
            'max_trade_size': float(os.getenv('MAX_TRADE_SIZE', '10')),  # in ETH
            'emergency_withdrawal_delay': 24 * 60 * 60,  # 24 hours
            'max_concurrent_trades': 3,
            'max_daily_trades': 50,
            'max_similar_pending_trades': 3,  # For MEV protection
            'min_liquidity_ratio': 3,  # Minimum ratio of pool liquidity to trade size
            'max_exposure_percentage': 20,  # Maximum portfolio exposure per trade
            'blacklisted_tokens': set(),  # Tokens to avoid
            'whitelist_only': True  # Only trade whitelisted tokens
        },
        'risk_management': {
            'position_sizing': {
                'base_size': float(os.getenv('BASE_POSITION_SIZE', '1')),  # in ETH
                'max_size': float(os.getenv('MAX_POSITION_SIZE', '10')),  # in ETH
                'size_increment': 0.1,  # Size increase step
                'max_portfolio_exposure': 0.2  # Maximum 20% of portfolio in one trade
            },
            'profit_management': {
                'min_profit_usd': 100,  # Minimum profit in USD
                'profit_threshold_multiplier': 1.5,  # Increase threshold after losses
                'take_profit': 0.03,  # 3% take profit
                'stop_loss': 0.01  # 1% stop loss
            },
            'risk_limits': {
                'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS', '0.1')),  # 10% max daily loss
                'max_drawdown': 0.2,  # 20% max drawdown
                'max_gas_cost_ratio': 0.1  # Max 10% of profit spent on gas
            }
        },
        'monitoring': {
            'performance': {
                'min_success_rate': 0.8,  # 80% minimum success rate
                'min_daily_profit': float(os.getenv('MIN_DAILY_PROFIT', '0.1')),  # in ETH
                'profit_window': 24 * 60 * 60,  # 24 hour window for profit calculation
                'max_gas_cost_ratio': 0.15  # Maximum 15% of profit spent on gas
            },
            'alerts': {
                'email': {
                    'enabled': True,
                    'smtp_server': os.getenv('SMTP_SERVER'),
                    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                    'username': os.getenv('SMTP_USERNAME'),
                    'password': os.getenv('SMTP_PASSWORD'),
                    'sender': os.getenv('ALERT_SENDER'),
                    'recipient': os.getenv('ALERT_RECIPIENT')
                },
                'telegram': {
                    'enabled': bool(os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'),
                    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                    'chat_id': os.getenv('TELEGRAM_CHAT_ID')
                },
                'cooldown': 300,  # 5 minutes between similar alerts
                'max_daily_alerts': 10  # Maximum alerts per day
            },
            'health_check': {
                'max_block_delay': 60,  # Maximum acceptable block delay in seconds
                'max_pending_tx': 10000,  # Maximum pending transactions in mempool
                'min_peer_count': 3,  # Minimum connected peers
                'check_interval': 60  # Check every minute
            }
        },
        'execution': {
            'max_retries': 3,
            'retry_delay': 10,  # seconds
            'timeout': 300,  # 5 minutes
            'confirmation_blocks': 2,
            'nonce_management': {
                'auto_increment': True,
                'reset_on_revert': True
            }
        },
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'file': 'arbitrage_bot.log',
            'max_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5,
            'console_output': True
        }
    }
