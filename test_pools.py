from web3 import Web3
import json
from decimal import Decimal

def test_pool(w3, pool_address, pool_abi):
    """Test interaction with a specific pool"""
    try:
        # Create contract instance
        contract = w3.eth.contract(
            address=w3.to_checksum_address(pool_address),
            abi=pool_abi
        )
        
        # Get slot0 data
        slot0 = contract.functions.slot0().call()
        sqrtPriceX96 = Decimal(str(slot0[0]))
        price = (sqrtPriceX96 / Decimal(str(2**96))) ** Decimal('2')
        
        # Get liquidity
        liquidity = contract.functions.liquidity().call()
        
        return {
            'price': float(price),
            'liquidity': liquidity,
            'status': 'success'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def main():
    # Initialize Web3 with Base mainnet
    w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org', request_kwargs={'timeout': 60}))
    
    # Check connection
    if not w3.is_connected():
        print("Failed to connect to Base network")
        return
        
    print(f"Connected to Base network")
    print(f"Latest block: {w3.eth.block_number}")
    
    # Pool ABI
    pool_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "slot0",
            "outputs": [
                {"name": "sqrtPriceX96", "type": "uint160"},
                {"name": "tick", "type": "int24"},
                {"name": "observationIndex", "type": "uint16"},
                {"name": "observationCardinality", "type": "uint16"},
                {"name": "observationCardinalityNext", "type": "uint16"},
                {"name": "feeProtocol", "type": "uint8"},
                {"name": "unlocked", "type": "bool"}
            ],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "liquidity",
            "outputs": [{"name": "", "type": "uint128"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Test pools
    pools = {
        'ETH/USDC': '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18',
        'WETH/USDC': '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18',
        'ETH/USDT': '0x205C7B1E69BeaF79FC0C39268B56F1FBD2c0Eb3A',
        'ETH/DAI': '0x6E7a7FF3964a5A516E0eE2b31D1eB1E2521d77c6',
        'USDC/USDT': '0x4Bd62356F6E052F7D2131bF3850C99907D1874D8',
        'USDC/DAI': '0x6E7a7FF3964a5A516E0eE2b31D1eB1E2521d77c6',
        'DAI/USDT': '0x9A4F3eD4F7C651cE5576dB8B95F6A59E58F6D937',
        'WBTC/USDC': '0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB',
        'WBTC/ETH': '0x2F3cE1B6C3F43a24850b98c2F661f0B76cF89E0b',
        'cbETH/ETH': '0x0d7c4b40018969f81750d0a164c3839a77353EFB',
        'UNI/USDC': '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18',
        'AAVE/USDC': '0x0d7c4b40018969f81750d0a164c3839a77353EFB',
        'SNX/USDC': '0x9A4F3eD4F7C651cE5576dB8B95F6A59E58F6D937'
    }
    
    print("\nTesting pools:")
    print("=" * 50)
    
    for name, address in pools.items():
        print(f"\nTesting {name} pool at {address}")
        result = test_pool(w3, address, pool_abi)
        
        if result['status'] == 'success':
            print(f"Success!")
            print(f"Price: {result['price']}")
            print(f"Liquidity: {result['liquidity']}")
        else:
            print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
