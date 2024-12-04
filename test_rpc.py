from web3 import Web3
import json

def test_connection():
    # Try different RPC endpoints
    endpoints = [
        'https://mainnet.base.org',
        'https://base-mainnet.g.alchemy.com/v2/demo',
        'https://base.blockpi.network/v1/rpc/public',
        'https://base.meowrpc.com'
    ]
    
    # Test pool address
    pool_address = '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18'  # ETH/USDC pool
    
    # UniswapV3 pool ABI (minimal)
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
        }
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}")
        try:
            w3 = Web3(Web3.HTTPProvider(endpoint, request_kwargs={'timeout': 60}))
            
            # Check connection
            if not w3.is_connected():
                print("Failed to connect")
                continue
                
            print("Connected successfully")
            
            # Try to get latest block
            block = w3.eth.block_number
            print(f"Latest block: {block}")
            
            # Try to interact with pool contract
            pool_contract = w3.eth.contract(
                address=w3.to_checksum_address(pool_address),
                abi=pool_abi
            )
            
            # Get current price
            slot0 = pool_contract.functions.slot0().call()
            sqrtPriceX96 = slot0[0]
            price = (sqrtPriceX96 / (2**96)) ** 2
            
            print(f"Pool price: {price}")
            print("Successfully interacted with pool contract")
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection()
