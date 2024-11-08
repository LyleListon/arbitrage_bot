t# mypy: disable-error-code="import,misc"
"""
Deploy contracts to mainnet with real Chainlink price feeds.
IMPORTANT: This system is designed ONLY for Uniswap V3. DO NOT use V2 contracts/routers.
"""
from typing import Tuple, Any, Dict, List
from eth_typing import ChecksumAddress
from web3 import Web3
from solcx import compile_standard, install_solc
import json
import os
from dotenv import load_dotenv
from eth_account import Account
from eth_account.signers.local import LocalAccount
import time


def get_next_nonce(w3: Web3, address: ChecksumAddress) -> int:
    """Get next nonce for address"""
    return w3.eth.get_transaction_count(address)


def compile_contract(
    contract_source_path: str,
    contract_name: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """Compile a Solidity contract with dependencies."""
    print("\nCompiling", contract_name)

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
                    "runs": 1000000  # Optimize for many runs to reduce gas
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


def deploy_contract(
    w3: Web3,
    account: LocalAccount,
    bytecode: str,
    abi: List[Dict[str, Any]],
    constructor_args: List[Any],
    contract_name: str
) -> Any:
    """Deploy a contract with enhanced error handling and verification."""
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Get optimal gas price
    gas_price = w3.eth.gas_price

    # Get fresh nonce
    next_nonce = get_next_nonce(w3, Web3.to_checksum_address(account.address))

    print("\nDeploying", contract_name)
    print("Constructor args:", constructor_args)

    # Estimate gas with minimal buffer
    estimated_gas = Contract.constructor(*constructor_args).estimate_gas({
        'from': account.address,
        'nonce': next_nonce
    })
    gas_limit = int(estimated_gas * 1.1)  # 10% buffer

    # Build and sign transaction
    constructor_txn = Contract.constructor(*constructor_args).build_transaction({
        'chainId': w3.eth.chain_id,
        'from': account.address,
        'nonce': next_nonce,
        'gas': gas_limit,
        'gasPrice': gas_price
    })

    print("\nTransaction details:")
    print("From:", account.address)
    print("Chain ID:", w3.eth.chain_id)
    print("Gas Price:", w3.from_wei(gas_price, 'gwei'), "Gwei")
    print("Gas Limit:", f"{gas_limit:,}")
    print("Estimated Cost:", w3.from_wei(gas_price * gas_limit, 'ether'), "ETH")

    # Ask for confirmation before sending transaction
    input("Press Enter to confirm deployment or Ctrl+C to cancel...")

    signed_txn = account.sign_transaction(constructor_txn)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("Transaction sent! Hash:", tx_hash.hex())

    # Wait for confirmation with timeout
    print("\nWaiting for deployment confirmation...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

    if tx_receipt['status'] == 1:
        print("✓ Contract deployed successfully at:", tx_receipt['contractAddress'])
        print("Gas Used:", f"{tx_receipt['gasUsed']:,}")
        print("Actual Cost:", w3.from_wei(tx_receipt['gasUsed'] * gas_price, 'ether'), "ETH")

        # Save deployment info
        deployment_info = {
            'address': tx_receipt['contractAddress'],
            'network': w3.eth.chain_id,
            'deployer': account.address,
            'timestamp': int(time.time()),
            'transaction_hash': tx_hash.hex(),
            'constructor_args': constructor_args,
            'gas_used': tx_receipt['gasUsed'],
            'gas_price': gas_price
        }

        os.makedirs('deployments', exist_ok=True)
        with open(f'deployments/{contract_name}_mainnet.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)

        return w3.eth.contract(
            address=tx_receipt['contractAddress'],
            abi=abi
        )
    else:
        raise Exception(f"Deployment failed for {contract_name}")


def setup_price_feeds(
    w3: Web3,
    price_feed_contract: Any,
    token_feeds: Dict[str, str],
    account: LocalAccount
) -> None:
    """Configure price feeds for tokens"""
    # Get optimal gas price
    gas_price = w3.eth.gas_price
    next_nonce = get_next_nonce(w3, Web3.to_checksum_address(account.address))

    print("\nSetting up price feeds...")
    for token, feed in token_feeds.items():
        print("\nConfiguring price feed for", token)
        print("Feed address:", feed)

        # Build transaction
        tx = price_feed_contract.functions.setPriceFeed(
            token,
            feed
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': next_nonce,
            'gas': 100000,  # Fixed gas limit for price updates
            'gasPrice': gas_price
        })

        print("Estimated cost:", w3.from_wei(gas_price * 100000, 'ether'), "ETH")
        input("Press Enter to confirm price feed setup or Ctrl+C to cancel...")

        # Sign and send transaction
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print("Transaction sent:", tx_hash.hex())

        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print("✓ Price feed set successfully")
            print("Gas Used:", f"{receipt['gasUsed']:,}")
        else:
            print("✗ Failed to set price feed")

        next_nonce += 1
        time.sleep(5)  # Wait between transactions


def setup_bot(
    w3: Web3,
    bot: Any,
    authorized_dexs: List[str],
    authorized_tokens: List[str],
    account: LocalAccount
) -> None:
    """Configure bot permissions"""
    # Get optimal gas price
    gas_price = w3.eth.gas_price
    next_nonce = get_next_nonce(w3, Web3.to_checksum_address(account.address))

    # First: DEX authorizations
    print("\nAuthorizing DEXs...")
    for dex in authorized_dexs:
        print("\nAuthorizing DEX", dex)

        tx = bot.functions.setAuthorizedDEX(
            dex,
            True
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': next_nonce,
            'gas': 100000,
            'gasPrice': gas_price
        })

        print("Estimated cost:", w3.from_wei(gas_price * 100000, 'ether'), "ETH")
        input("Press Enter to confirm DEX authorization or Ctrl+C to cancel...")

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print("Transaction sent:", tx_hash.hex())

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print("✓ DEX authorized")
        else:
            print("✗ Failed to authorize DEX")

        next_nonce += 1
        time.sleep(5)

    # Second: Token authorizations
    print("\nAuthorizing tokens...")
    for token in authorized_tokens:
        print("\nAuthorizing token", token)

        tx = bot.functions.setAuthorizedToken(
            token,
            True
        ).build_transaction({
            'chainId': w3.eth.chain_id,
            'from': account.address,
            'nonce': next_nonce,
            'gas': 100000,
            'gasPrice': gas_price
        })

        print("Estimated cost:", w3.from_wei(gas_price * 100000, 'ether'), "ETH")
        input("Press Enter to confirm token authorization or Ctrl+C to cancel...")

        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print("Transaction sent:", tx_hash.hex())

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            print("✓ Token authorized")
        else:
            print("✗ Failed to authorize token")

        next_nonce += 1
        time.sleep(5)


def main() -> None:
    """Deploy and configure contracts"""
    # Load mainnet configuration
    load_dotenv('.env.mainnet')

    # Initialize Web3
    rpc_url = os.getenv('MAINNET_RPC_URL')
    if not rpc_url:
        raise ValueError("MAINNET_RPC_URL not found in environment")

    print("Deploying to MAINNET")
    print("RPC URL:", rpc_url)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise Exception("Failed to connect to mainnet")

    print("Connected to network. Chain ID:", w3.eth.chain_id)

    # Load account
    private_key = os.getenv('MAINNET_PRIVATE_KEY')
    if not private_key:
        raise ValueError("MAINNET_PRIVATE_KEY not found in environment")

    # Remove '0x' prefix if present and convert to bytes
    clean_key = private_key.replace('0x', '')
    key_bytes = bytes.fromhex(clean_key)
    account = Account.from_key(key_bytes)
    print("Using address:", account.address)

    balance = w3.eth.get_balance(account.address)
    print("Account balance:", w3.from_wei(balance, 'ether'), "ETH")

    if balance == 0:
        raise ValueError("Account has no balance")

    try:
        # Deploy PriceFeedIntegration
        feed_bytecode, feed_abi = compile_contract(
            'contracts/PriceFeedIntegration.sol',
            'PriceFeedIntegration'
        )

        price_feed = deploy_contract(
            w3, account, feed_bytecode, feed_abi,
            [],  # No constructor args
            'PriceFeedIntegration'
        )

        # Configure price feeds with mainnet Chainlink addresses
        token_feeds = {
            str(Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')):  # WETH
            str(Web3.to_checksum_address('0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419')),  # ETH/USD

            str(Web3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')):  # USDC
            str(Web3.to_checksum_address('0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6')),  # USDC/USD

            str(Web3.to_checksum_address('0x514910771AF9Ca656af840dff83E8264EcF986CA')):  # LINK
            str(Web3.to_checksum_address('0x2c1d072e956AFFC0D435Cb7AC38EF18d24d9127c')),  # LINK/USD

            str(Web3.to_checksum_address('0x6B175474E89094C44Da98b954EedeAC495271d0F')):  # DAI
            str(Web3.to_checksum_address('0xAed0c38402a5d19df6E4c03F4E2DceD6e29c1ee9'))   # DAI/USD
        }
        setup_price_feeds(w3, price_feed, token_feeds, account)

        # Deploy ArbitrageBot with updated parameters
        bot_bytecode, bot_abi = compile_contract(
            'contracts/ArbitrageBot.sol',
            'ArbitrageBot'
        )

        min_profit_basis_points = 100  # 1% minimum profit
        max_trade_size = w3.to_wei(0.2, 'ether')  # 0.2 ETH max trade
        emergency_withdrawal_delay = 24 * 60 * 60  # 24 hours

        bot = deploy_contract(
            w3, account, bot_bytecode, bot_abi,
            [min_profit_basis_points, max_trade_size, emergency_withdrawal_delay],
            'ArbitrageBot'
        )

        # Configure authorized DEXs (Uniswap V3 only) and tokens
        authorized_dexs = [
            # Uniswap V3 Router ONLY - Do not use V2
            str(Web3.to_checksum_address('0xE592427A0AEce92De3Edee1F18E0157C05861564'))
        ]

        authorized_tokens = [
            str(Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')),  # WETH
            str(Web3.to_checksum_address('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')),  # USDC
            str(Web3.to_checksum_address('0x514910771AF9Ca656af840dff83E8264EcF986CA')),  # LINK
            str(Web3.to_checksum_address('0x6B175474E89094C44Da98b954EedeAC495271d0F'))   # DAI
        ]

        setup_bot(w3, bot, authorized_dexs, authorized_tokens, account)

        print("\nDeployment Summary on MAINNET:")
        print("-" * 50)
        print("PriceFeedIntegration:", price_feed.address)
        print("ArbitrageBot:", bot.address)
        print("\nAdd these addresses to your environment file:")
        print("MAINNET_PRICE_FEED_ADDRESS=", price_feed.address)
        print("MAINNET_BOT_ADDRESS=", bot.address)

    except Exception as e:
        print("\n✗ Deployment failed:", str(e))
        raise


if __name__ == '__main__':
    main()
