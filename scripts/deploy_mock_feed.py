"""
Script to deploy mock price feed contract
"""
import os
from web3 import Web3
from eth_account import Account
from solcx import compile_standard, install_solc
from dotenv import load_dotenv
import json


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
                    "runs": 200
                },
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                },
                "remappings": [
                    f"@openzeppelin/={os.path.join(node_modules, '@openzeppelin')}/"
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


def deploy_contract(w3, account, bytecode, abi):
    """Deploy a contract"""
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build transaction
    tx = Contract.constructor().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    })
    
    # Sign transaction
    signed = w3.eth.account.sign_transaction(tx, account.key)
    
    # Send transaction
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print(f"✅ Contract deployed successfully at: {receipt.contractAddress}")
        return receipt.contractAddress
    else:
        raise Exception("Contract deployment failed")


def update_env_file(contract_address):
    """Update environment file with new contract address"""
    env_file = '.env.holesky'
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    with open(env_file, 'w') as f:
        for line in lines:
            if line.startswith('HOLESKY_PRICE_FEED_ADDRESS='):
                f.write(f'HOLESKY_PRICE_FEED_ADDRESS={contract_address}\n')
            else:
                f.write(line)


def main():
    """Deploy mock price feed contract"""
    # Load environment variables
    load_dotenv('.env.holesky')
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    if not w3.is_connected():
        raise Exception("Failed to connect to network")
    
    print(f"Connected to network. Chain ID: {w3.eth.chain_id}")
    
    # Load account
    account = Account.from_key(os.getenv('HOLESKY_PRIVATE_KEY'))
    print(f"Using address: {account.address}")
    
    try:
        # Compile and deploy contract
        bytecode, abi = compile_contract(
            'contracts/MockPriceFeed.sol',
            'MockPriceFeed'
        )
        
        contract_address = deploy_contract(w3, account, bytecode, abi)
        
        # Update environment file
        update_env_file(contract_address)
        print("\nEnvironment file updated with new contract address")
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")


if __name__ == "__main__":
    main()
