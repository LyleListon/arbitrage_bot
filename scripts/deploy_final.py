"""
Deploy contracts with mock price feeds for testing
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
    
    with open(contract_source_path, 'r') as f:
        contract_source = f.read()

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


def deploy_contract(w3, account, bytecode, abi, constructor_args, contract_name):
    """Deploy a contract with enhanced error handling and verification."""
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Get optimal gas price
    gas_price = w3.eth.gas_price
    
    # Get fresh nonce
    nonce = w3.eth.get_transaction_count(account.address)
    
    print(f"\nDeploying {contract_name}...")
    print(f"Constructor args: {constructor_args}")
    
    # Estimate gas with minimal buffer
    estimated_gas = Contract.constructor(*constructor_args).estimate_gas({
        'from': account.address,
        'nonce': nonce
    })
    gas_limit = int(estimated_gas * 1.1)  # 10% buffer
    
    # Build and sign transaction
    constructor_txn = Contract.constructor(*constructor_args).build_transaction({
        'chainId': w3.eth.chain_id,
        'from': account.address,
        'nonce': nonce,
        'gas': gas_limit,
        'gasPrice': gas_price
    })
    
    print("\nTransaction details:")
    print(f"From: {account.address}")
    print(f"Chain ID: {w3.eth.chain_id}")
    print(f"Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
    print(f"Gas Limit: {gas_limit:,}")
    print(f"Estimated Cost: {w3.from_wei(gas_price * gas_limit, 'ether'):.6f} ETH")
    
    # Ask for confirmation before sending transaction
    input("Press Enter to confirm deployment or Ctrl+C to cancel...")
    
    signed_txn = account.sign_transaction(constructor_txn)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Transaction sent! Hash: {tx_hash.hex()}")
    
    # Wait for confirmation with timeout
    print("\nWaiting for deployment confirmation...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if tx_receipt.status == 1:
        print(f"✓ Contract deployed successfully at: {tx_receipt.contractAddress}")
        print(f"Gas Used: {tx_receipt.gasUsed:,}")
        print(f"Actual Cost: {w3.from_wei(tx_receipt.gasUsed * gas_price, 'ether'):.6f} ETH")
        
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
        with open(f'deployments/{contract_name}_holesky.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        return w3.eth.contract(
            address=tx_receipt.contractAddress,
            abi=abi
        )
    else:
        raise Exception(f"Deployment failed for {contract_name}")


def setup_mock_prices(w3, mock_feed, token_prices, account):
    """Set up mock prices for tokens"""
    # Get optimal gas price
    gas_price = w3.eth.gas_price
    nonce = w3.eth.get_transaction_count(account.address)
    
    print("\nSetting up mock prices...")
    for token, (price, decimals) in token_prices.items():
        print(f"\nSetting up {token} price:")
        print(f"Price: ${price/10**decimals:.2f}")
        print(f"Decimals: {decimals}")
        
        # Build transaction
        tx = mock_feed.functions.setPrice(
            token,
            price,
            decimals
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,  # Fixed gas limit for price updates
            'gasPrice': gas_price
        })
        
        # Sign and send transaction
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent: {tx_hash.hex()}")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"✓ Price set successfully")
            print(f"Gas Used: {receipt.gasUsed:,}")
        else:
            print(f"✗ Failed to set price")
        
        nonce += 1
        time.sleep(5)  # Wait between transactions


def setup_bot(w3, bot, authorized_dexs, authorized_tokens, account):
    """Configure bot permissions"""
    # Get optimal gas price
    gas_price = w3.eth.gas_price
    nonce = w3.eth.get_transaction_count(account.address)
    
    # First: DEX authorizations
    print("\nAuthorizing DEXs...")
    for dex in authorized_dexs:
        print(f"\nAuthorizing DEX {dex}")
        
        tx = bot.functions.setAuthorizedDEX(
            dex,
            True
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': gas_price
        })
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"✓ DEX authorized")
        else:
            print(f"✗ Failed to authorize DEX")
        
        nonce += 1
        time.sleep(5)
    
    # Second: Token authorizations
    print("\nAuthorizing tokens...")
    for token in authorized_tokens:
        print(f"\nAuthorizing token {token}")
        
        tx = bot.functions.setAuthorizedToken(
            token,
            True
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': gas_price
        })
        
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent: {tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            print(f"✓ Token authorized")
        else:
            print(f"✗ Failed to authorize token")
        
        nonce += 1
        time.sleep(5)


def main():
    """Deploy and configure contracts"""
    # Load Holesky configuration
    load_dotenv('.env.holesky')
    
    # Initialize Web3
    rpc_url = os.getenv('HOLESKY_RPC_URL')
    if not rpc_url:
        raise ValueError("HOLESKY_RPC_URL not found in environment")
    
    print(f"Deploying to HOLESKY")
    print(f"RPC URL: {rpc_url}")
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise Exception("Failed to connect to Holesky")
    
    print(f"Connected to network. Chain ID: {w3.eth.chain_id}")
    
    # Load account
    private_key = os.getenv('HOLESKY_PRIVATE_KEY')
    if not private_key:
        raise ValueError("HOLESKY_PRIVATE_KEY not found in environment")
    
    account = Account.from_key(private_key)
    print(f"Using address: {account.address}")
    
    balance = w3.eth.get_balance(account.address)
    print(f"Account balance: {w3.from_wei(balance, 'ether')} ETH")
    
    if balance == 0:
        raise ValueError("Account has no balance")
    
    try:
        # Deploy MockPriceFeed
        feed_bytecode, feed_abi = compile_contract(
            'contracts/MockPriceFeed.sol',
            'MockPriceFeed'
        )
        
        mock_feed = deploy_contract(
            w3, account, feed_bytecode, feed_abi,
            [],  # No constructor args
            'MockPriceFeed'
        )
        
        # Set up mock prices
        token_prices = {
            Web3.to_checksum_address('0x94373a4919B3240D86eA41593D5eBa789FEF3848'): (2000 * 10**8, 8),  # WETH $2000
            Web3.to_checksum_address('0x9C4073e98dA7d92427B550Dc10e919dC54C3a61F'): (1 * 10**8, 8)      # USDC $1
        }
        setup_mock_prices(w3, mock_feed, token_prices, account)
        
        # Deploy ArbitrageBot
        bot_bytecode, bot_abi = compile_contract(
            'contracts/ArbitrageBot.sol',
            'ArbitrageBot'
        )
        
        min_profit_basis_points = 200  # 2% minimum profit
        max_trade_size = w3.to_wei(0.1, 'ether')  # 0.1 ETH max trade
        emergency_withdrawal_delay = 24 * 60 * 60  # 24 hours
        
        bot = deploy_contract(
            w3, account, bot_bytecode, bot_abi,
            [min_profit_basis_points, max_trade_size, emergency_withdrawal_delay],
            'ArbitrageBot'
        )
        
        # Configure bot
        authorized_dexs = [
            Web3.to_checksum_address('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')  # Uniswap V2 Router
        ]
        
        authorized_tokens = [
            Web3.to_checksum_address('0x94373a4919B3240D86eA41593D5eBa789FEF3848'),  # WETH
            Web3.to_checksum_address('0x9C4073e98dA7d92427B550Dc10e919dC54C3a61F')   # USDC
        ]
        
        setup_bot(w3, bot, authorized_dexs, authorized_tokens, account)
        
        print(f"\nDeployment Summary on HOLESKY:")
        print("-" * 50)
        print(f"MockPriceFeed: {mock_feed.address}")
        print(f"ArbitrageBot: {bot.address}")
        print("\nAdd these addresses to your environment file:")
        print(f"HOLESKY_PRICE_FEED_ADDRESS={mock_feed.address}")
        print(f"HOLESKY_BOT_ADDRESS={bot.address}")
        
    except Exception as e:
        print(f"\n✗ Deployment failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()
