# mypy: disable-error-code="import,misc"
"""
Deploy contracts to Sepolia testnet or mainnet.
IMPORTANT: This system is designed ONLY for Uniswap V3. DO NOT use V2 contracts/routers.
"""
from typing import (
    Tuple, Any, Dict, List, TypedDict, Optional, Union
)
from eth_typing import ChecksumAddress
from web3 import Web3
from solcx import compile_standard, install_solc
import json
import os
from os import PathLike
from dotenv import load_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount
import time
import argparse


class NetworkTokens(TypedDict, total=True):
    WETH: str
    USDC: str
    LINK: str
    DAI: str


class NetworkPriceFeeds(TypedDict, total=True):
    ETH_USD: str  # Using underscore instead of slash for valid Python identifier
    USDC_USD: str
    LINK_USD: str
    DAI_USD: str


class NetworkDex(TypedDict, total=True):
    router: str


class NetworkSettings(TypedDict, total=True):
    min_profit_basis_points: int
    max_trade_size: float
    emergency_delay: int


class NetworkConfig(TypedDict, total=True):
    env_file: str
    rpc_key: str
    key_key: str
    tokens: NetworkTokens
    price_feeds: NetworkPriceFeeds
    dex: NetworkDex
    settings: NetworkSettings


# Network configurations
NETWORKS: Dict[str, NetworkConfig] = {
    'sepolia': {
        'env_file': '.env.sepolia',
        'rpc_key': 'SEPOLIA_RPC_URL',
        'key_key': 'SEPOLIA_PRIVATE_KEY',
        'tokens': {
            'WETH': '0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14',
            'USDC': '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
            'LINK': '0x779877A7B0D9E8603169DdbD7836e478b4624789',
            'DAI': '0x68194a729C2450ad26072b3D33ADaCbcef39D574'
        },
        'price_feeds': {
            'ETH_USD': '0x694AA1769357215DE4FAC081bf1f309aDC325306',
            'USDC_USD': '0xA2F78ab2355fe2f984D808B5CeE7FD0A93D5270E',
            'LINK_USD': '0xc59E3633BAAC79493d908e63626716e204A45EdF',
            'DAI_USD': '0x14866185B1962B63C3Ea9E03Bc1da838bab34C19'
        },
        'dex': {
            'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564'  # Uniswap V3
        },
        'settings': {
            'min_profit_basis_points': 50,  # 0.5% for testnet
            'max_trade_size': 0.1,  # 0.1 ETH for testnet
            'emergency_delay': 1 * 60 * 60  # 1 hour for testnet
        }
    },
    'mainnet': {
        'env_file': '.env.mainnet',
        'rpc_key': 'MAINNET_RPC_URL',
        'key_key': 'MAINNET_PRIVATE_KEY',
        'tokens': {
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'LINK': '0x514910771AF9Ca656af840dff83E8264EcF986CA',
            'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F'
        },
        'price_feeds': {
            'ETH_USD': '0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419',
            'USDC_USD': '0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6',
            'LINK_USD': '0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c',
            'DAI_USD': '0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9'
        },
        'dex': {
            'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564'  # Uniswap V3
        },
        'settings': {
            'min_profit_basis_points': 100,  # 1% for mainnet
            'max_trade_size': 0.2,  # 0.2 ETH for mainnet
            'emergency_delay': 24 * 60 * 60  # 24 hours for mainnet
        }
    }
}


def create_account_from_key(private_key: str) -> LocalAccount:
    """Create an account from a private key"""
    # Remove '0x' prefix if present and convert to bytes
    clean_key = private_key.replace('0x', '')
    key_bytes = bytes.fromhex(clean_key)
    # Create account using static method
    return Account.from_key(key_bytes)  # type: ignore[no-any-return]


def get_next_nonce(w3: Web3, address: ChecksumAddress) -> int:
    """Get next nonce for address"""
    return w3.eth.get_transaction_count(address)
