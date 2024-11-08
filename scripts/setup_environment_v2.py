"""
Script to set up the development environment and deploy contracts
"""
import os
from solcx import install_solc, compile_standard, get_installed_solc_versions
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv
import json
import time


def ensure_solc():
    """Ensure solc is installed"""
    version = "0.8.19"
    if version not in [str(v) for v in get_installed_solc_versions()]:
        print(f"Installing solc version {version}...")
        install_solc(version)
    return version


def send_transaction(w3: Web3, account: LocalAccount, transaction):
    """Send a transaction and wait for receipt"""
    signed = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return w3.eth.wait_for_transaction_receipt(tx_hash)


def compile_contract(contract_source_path, contract_name, solc_version):
    """Compile a Solidity contract with dependencies."""
    print(f"\nCompiling {contract_name}...")
    
    with open(contract_source_path, 'r') as file:
        contract_source = file.read()
    
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
        allow_paths=[base_path, node_modules, contracts],
        solc_version=solc_version
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


def deploy_contract(w3, account, bytecode, abi, constructor_args, contract_name):
    """Deploy a contract with enhanced error handling and verification."""
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    max_retries = 3
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            # Get current gas price with dynamic premium
            base_gas_price = w3.eth.gas_price
            gas_price = int(base_gas_price * 1.1)  # 10% premium
            
            # Ensure gas price doesn't exceed limit
            max_gas_price = w3.to_wei(50, 'gwei')
            if gas_price > max_gas_price:
                gas_price = max_gas_price
            
            # Get fresh nonce
            nonce = w3.eth.get_transaction_count(account.address)
            
            print(f"\nDeploying {contract_name}...")
            print(f"Attempt {attempt + 1} of {max_retries}")
            print(f"Constructor args: {constructor_args}")
            
            # Build transaction
            constructor_txn = Contract.constructor(*constructor_args).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': 2000000,  # Fixed gas limit for deployment
                'gasPrice': gas_price,
                'chainId': w3.eth.chain_id
            })
            
            print("\nTransaction details:")
            print(f"From: {account.address}")
            print(f"Chain ID: {w3.eth.chain_id}")
            print(f"Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
            print(f"Gas Limit: 2,000,000")
            
            # Send transaction
            tx_receipt = send_transaction(w3, account, constructor_txn)
            
            if tx_receipt.status == 1:
                print(f"✅ Contract deployed successfully at: {tx_receipt.contractAddress}")
                
                # Save deployment info
                deployment_info = {
                    'address': tx_receipt.contractAddress,
                    'network': w3.eth.chain_id,
                    'deployer': account.address,
                    'timestamp': int(time.time()),
                    'transaction_hash': tx_receipt.transactionHash.hex(),
                    'constructor_args': constructor_args,
                    'gas_used': tx_receipt.gasUsed,
                    'gas_price': gas_price
                }
                
                os.makedirs('deployments', exist_ok=True)
                network = os.getenv('DEPLOY_NETWORK', 'holesky')
                with open(f'deployments/{contract_name}_{network}.json', 'w') as f:
                    json.dump(deployment_info, f, indent=2)
                
                return w3.eth.contract(
                    address=tx_receipt.contractAddress,
                    abi=abi
                )
            else:
                print(f"❌ Deployment failed on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                continue
                
        except Exception as e:
            print(f"\n❌ Error on attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                raise Exception(f"Failed to deploy {contract_name} after {max_retries} attempts")


def setup_mock_prices(w3, mock_feed, account):
    """Set up initial mock prices"""
    try:
        # Set WETH price to $2000
        print("\nSetting WETH price...")
        weth_price = 2000 * 10**8  # $2000 with 8 decimals
        tx = mock_feed.functions.setPrice(
            os.getenv('WETH_ADDRESS'),
            weth_price,
            8  # decimals
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price,
            'gas': 200000
        })
        
        tx_receipt = send_transaction(w3, account, tx)
        if tx_receipt.status == 1:
            print("✅ WETH price set successfully")
        else:
            print("❌ Failed to set WETH price")
            return
        
        # Set USDC price to $1
        print("\nSetting USDC price...")
        usdc_price = 1 * 10**8  # $1 with 8 decimals
        tx = mock_feed.functions.setPrice(
            os.getenv('USDC_ADDRESS'),
            usdc_price,
            8  # decimals
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price,
            'gas': 200000
        })
        
        tx_receipt = send_transaction(w3, account, tx)
        if tx_receipt.status == 1:
            print("✅ USDC price set successfully")
        else:
            print("❌ Failed to set USDC price")
        
    except Exception as e:
        print(f"❌ Error setting up mock prices: {str(e)}")


def update_env_file(mock_feed_address):
    """Update environment file with new contract address"""
    env_file = '.env.holesky'
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Replace old mock feed address with new one
    env_content = env_content.replace(
        f"HOLESKY_PRICE_FEED_ADDRESS={os.getenv('HOLESKY_PRICE_FEED_ADDRESS')}",
        f"HOLESKY_PRICE_FEED_ADDRESS={mock_feed_address}"
    )
    
    with open(env_file, 'w') as f:
        f.write(env_content)


def main():
    """Set up environment and deploy contracts"""
    # Install solc
    solc_version = ensure_solc()
    print(f"Using solc version: {solc_version}")
    
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
    
    balance = w3.eth.get_balance(account.address)
    print(f"Account balance: {w3.from_wei(balance, 'ether')} ETH")
    
    if balance == 0:
        raise ValueError("Account has no balance")
    
    try:
        # Deploy MockPriceFeed
        mock_bytecode, mock_abi = compile_contract(
            'contracts/MockPriceFeed.sol',
            'MockPriceFeed',
            solc_version
        )
        
        mock_feed = deploy_contract(
            w3, account, mock_bytecode, mock_abi,
            [],  # No constructor args
            'MockPriceFeed'
        )
        
        # Set up mock prices
        setup_mock_prices(w3, mock_feed, account)
        
        # Update environment file
        update_env_file(mock_feed.address)
        
        print("\nDeployment Summary:")
        print("-" * 50)
        print(f"MockPriceFeed: {mock_feed.address}")
        print("\nEnvironment file updated with new address")
        print("\nSetup complete! You can now restart the dashboard.")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
