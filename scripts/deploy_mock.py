"""
Deploy script for mock contracts
"""
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
            
            # Estimate gas with buffer
            estimated_gas = Contract.constructor(*constructor_args).estimate_gas({
                'from': account.address,
                'nonce': nonce
            })
            gas_limit = int(estimated_gas * 1.2)  # 20% buffer
            
            # Build and sign transaction
            constructor_txn = Contract.constructor(*constructor_args).build_transaction({
                'from': account.address,
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'chainId': w3.eth.chain_id
            })
            
            print("\nTransaction details:")
            print(f"From: {account.address}")
            print(f"Chain ID: {w3.eth.chain_id}")
            print(f"Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
            print(f"Gas Limit: {gas_limit:,}")
            
            signed_txn = account.sign_transaction(constructor_txn)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Transaction sent! Hash: {tx_hash.hex()}")
            
            # Wait for confirmation
            print("\nWaiting for deployment confirmation...")
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt.status == 1:
                print(f"✅ Contract deployed successfully at: {tx_receipt.contractAddress}")
                
                # Save deployment info
                deployment_info = {
                    'address': tx_receipt.contractAddress,
                    'network': w3.eth.chain_id,
                    'deployer': account.address,
                    'timestamp': int(time.time()),
                    'transaction_hash': tx_hash.hex(),
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
    """Set up mock prices for testing"""
    try:
        # Set WETH price to $2000
        weth_price = 2000 * 10**8  # 8 decimals
        tx = mock_feed.functions.setPrice(
            os.getenv('WETH_ADDRESS'),
            weth_price,
            8  # decimals
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("✅ WETH price set successfully")
        
        # Set USDC price to $1
        usdc_price = 1 * 10**8  # 8 decimals
        tx = mock_feed.functions.setPrice(
            os.getenv('USDC_ADDRESS'),
            usdc_price,
            8  # decimals
        ).build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gasPrice': w3.eth.gas_price
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("✅ USDC price set successfully")
        
    except Exception as e:
        print(f"❌ Error setting mock prices: {str(e)}")


def main():
    """Deploy mock contracts"""
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
            'MockPriceFeed'
        )
        
        mock_feed = deploy_contract(
            w3, account, mock_bytecode, mock_abi,
            [],  # No constructor args
            'MockPriceFeed'
        )
        
        # Set up mock prices
        setup_mock_prices(w3, mock_feed, account)
        
        # Deploy ArbitrageBot with mock feed
        bot_bytecode, bot_abi = compile_contract(
            'contracts/ArbitrageBot.sol',
            'ArbitrageBot'
        )
        
        min_profit_basis_points = 200  # 2% minimum profit
        max_trade_size = w3.to_wei(0.1, 'ether')  # 0.1 ETH max trade for testnet
        emergency_withdrawal_delay = 24 * 60 * 60  # 24 hours
        
        bot = deploy_contract(
            w3, account, bot_bytecode, bot_abi,
            [min_profit_basis_points, max_trade_size, emergency_withdrawal_delay],
            'ArbitrageBot'
        )
        
        # Configure authorized DEXs and tokens
        authorized_dexs = [
            os.getenv('UNISWAP_V2_ROUTER')  # Uniswap V2 Router on Holesky
        ]
        
        authorized_tokens = [
            os.getenv('WETH_ADDRESS'),
            os.getenv('USDC_ADDRESS')
        ]
        
        # Set up authorizations
        for dex in authorized_dexs:
            tx = bot.functions.setAuthorizedDEX(
                dex,
                True
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gasPrice': w3.eth.gas_price
            })
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"✅ Authorized DEX {dex}")
        
        for token in authorized_tokens:
            tx = bot.functions.setAuthorizedToken(
                token,
                True
            ).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gasPrice': w3.eth.gas_price
            })
            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"✅ Authorized token {token}")
        
        print(f"\nDeployment Summary:")
        print("-" * 50)
        print(f"MockPriceFeed: {mock_feed.address}")
        print(f"ArbitrageBot: {bot.address}")
        print("\nAdd these addresses to your environment file:")
        print(f"HOLESKY_PRICE_FEED_ADDRESS={mock_feed.address}")
        print(f"HOLESKY_BOT_ADDRESS={bot.address}")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
