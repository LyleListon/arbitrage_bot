from web3 import Web3
from solcx import compile_standard, install_solc
import json
import os
from dotenv import load_dotenv
from eth_account import Account
import time


def compile_contract(contract_source_path, contract_name):
    """Compile a Solidity contract with dependencies."""
    print(f"\nCompiling {contract_name}...")
    
    with open(contract_source_path, 'r') as file:
        contract_source = file.read()

    # Install specific solc version
    install_solc('0.8.19')
    
    # Get base path for imports
    base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    node_modules = os.path.join(base_path, "node_modules")
    contracts = os.path.join(base_path, "contracts")
    
    # Compile with proper settings and dependencies
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                f"{contract_name}.sol": {"content": contract_source}
            },
            "settings": {
                "optimizer": {
                    "enabled": True,
                    "runs": 1000000
                },
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                },
                "remappings": [
                    f"@openzeppelin/={os.path.join(node_modules, '@openzeppelin')}/",
                    f"@chainlink/={os.path.join(node_modules, '@chainlink')}/"
                ]
            }
        },
        allow_paths=[base_path, node_modules, contracts]
    )

    # Save ABI
    contract_interface = compiled_sol['contracts'][f"{contract_name}.sol"][contract_name]
    abi = json.loads(contract_interface['metadata'])['output']['abi']
    
    os.makedirs('abi', exist_ok=True)
    with open(f'abi/{contract_name}.json', 'w') as f:
        json.dump(abi, f, indent=2)

    return (
        contract_interface['evm']['bytecode']['object'],
        abi
    )


def main():
    # Load environment and connect to Holesky
    load_dotenv('.env.holesky')
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    print(f"Connected to Holesky: {w3.is_connected()}")
    
    # Load account
    account = w3.eth.account.from_key(os.getenv('HOLESKY_PRIVATE_KEY'))
    print(f"Using account: {account.address}")
    
    # Compile contract
    bytecode, abi = compile_contract('contracts/MockPriceFeed.sol', 'MockPriceFeed')
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Deploy contract
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    # Build deployment transaction
    tx = Contract.constructor().build_transaction({
        'chainId': w3.eth.chain_id,
        'from': account.address,
        'nonce': nonce,
        'gasPrice': gas_price,
        'gas': 2000000  # High gas limit for deployment
    })
    
    # Sign and send transaction
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Deployment transaction sent: {tx_hash.hex()}")
    
    # Wait for confirmation
    print("Waiting for deployment confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = receipt.contractAddress
    print(f"Contract deployed at: {contract_address}")
    
    # Save deployment info
    deployment_info = {
        'address': contract_address,
        'deployer': account.address,
        'timestamp': int(time.time()),
        'transaction_hash': tx_hash.hex()
    }
    
    os.makedirs('deployments', exist_ok=True)
    with open('deployments/MockPriceFeed_holesky.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    # Update .env.holesky with new address
    env_path = '.env.holesky'
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Replace or add the contract address
    if 'HOLESKY_PRICE_FEED_ADDRESS=' in env_content:
        env_content = '\n'.join([
            line if not line.startswith('HOLESKY_PRICE_FEED_ADDRESS=') else f'HOLESKY_PRICE_FEED_ADDRESS={contract_address}'
            for line in env_content.split('\n')
        ])
    else:
        env_content += f'\nHOLESKY_PRICE_FEED_ADDRESS={contract_address}'
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("\nDeployment complete!")
    print(f"Contract address: {contract_address}")
    print("Environment file updated")
    
    # Initialize with test prices
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    # Set up test prices
    token_prices = {
        'WETH': (os.getenv('WETH_ADDRESS'), int(2000 * 10**8)),  # $2000
        'USDC': (os.getenv('USDC_ADDRESS'), int(1 * 10**8))      # $1
    }
    
    print("\nSetting up initial prices...")
    nonce = w3.eth.get_transaction_count(account.address)
    
    for name, (token, price) in token_prices.items():
        print(f"\nSetting {name} price:")
        print(f"Token: {token}")
        print(f"Price: ${price/10**8:.2f}")
        
        tx = contract.functions.setPrice(
            token,
            price,
            8  # 8 decimals
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gasPrice': gas_price,
            'gas': 200000
        })
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print("✓ Price set successfully")
        else:
            print("✗ Failed to set price")
        
        nonce += 1
        time.sleep(5)  # Wait between transactions


if __name__ == '__main__':
    main()
