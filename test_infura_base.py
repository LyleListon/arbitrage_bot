from web3 import Web3
from decimal import Decimal

def main():
    # Infura endpoint for Base
    infura_url = "https://base-mainnet.infura.io/v3/863c326dab1a444dba3f41ae7a07ccce"
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(infura_url, request_kwargs={'timeout': 60}))
    
    # Check connection
    if not w3.is_connected():
        print("Failed to connect to Base network")
        return
    
    print(f"Connected to Base network")
    print(f"Latest block: {w3.eth.block_number}")
    
    # Test ETH/USDC pool
    pool_address = '0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18'
    
    # Pool ABI (minimal)
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
    
    try:
        # Create contract instance
        contract = w3.eth.contract(
            address=w3.to_checksum_address(pool_address),
            abi=pool_abi
        )
        
        # Get current price
        slot0 = contract.functions.slot0().call()
        sqrtPriceX96 = Decimal(str(slot0[0]))
        price = (sqrtPriceX96 / Decimal(str(2**96))) ** Decimal('2')
        
        # Convert to USD terms
        eth_price = Decimal('1') / price
        
        print(f"\nETH/USDC Pool:")
        print(f"Pool Address: {pool_address}")
        print(f"ETH Price: ${eth_price:,.2f}")
        print(f"Success!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
