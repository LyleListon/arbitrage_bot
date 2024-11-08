"""
Compile ArbitrageBotV2 contract
"""
from solcx import compile_standard, install_solc
import json
import os


def main():
    print("\n🔧 Compiling ArbitrageBotV2")
    print("=" * 50)
    
    # Install specific solc version
    print("\nInstalling solc 0.8.19...")
    install_solc('0.8.19')
    
    # Read contract source
    print("\nReading contract source...")
    with open('contracts/ArbitrageBotV2.sol', 'r') as f:
        contract_source = f.read()
    
    # Get base path for imports
    base_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    node_modules = os.path.join(base_path, "node_modules")
    contracts = os.path.join(base_path, "contracts")
    
    print("\nCompiling contract...")
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "ArbitrageBotV2.sol": {"content": contract_source}
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
    
    # Extract contract data
    contract_interface = compiled_sol['contracts']['ArbitrageBotV2.sol']['ArbitrageBotV2']
    bytecode = contract_interface['evm']['bytecode']['object']
    abi = json.loads(contract_interface['metadata'])['output']['abi']
    
    # Save compilation output
    os.makedirs('build', exist_ok=True)
    
    print("\nSaving bytecode...")
    with open('build/ArbitrageBotV2.bin', 'w') as f:
        f.write(bytecode)
    
    print("Saving ABI...")
    with open('build/ArbitrageBotV2.abi', 'w') as f:
        json.dump(abi, f, indent=2)
    
    # Save deployment info
    deployment_info = {
        'version': 'v2',
        'solidity_version': '0.8.19',
        'optimizer_runs': 1000000,
        'constructor_args': {
            'min_profit_basis_points': 200,  # 2% minimum profit
            'max_trade_size': '0.1 ETH',
            'emergency_withdrawal_delay': '24 hours'
        },
        'features': [
            'Flash swap capability',
            'Gas optimization',
            'Enhanced security',
            'Better simulation functions',
            'Improved error handling'
        ],
        'dependencies': [
            '@openzeppelin/contracts/security/ReentrancyGuard.sol',
            '@openzeppelin/contracts/security/Pausable.sol',
            '@openzeppelin/contracts/access/Ownable.sol',
            '@openzeppelin/contracts/token/ERC20/IERC20.sol',
            '@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol'
        ]
    }
    
    print("Saving deployment info...")
    with open('build/deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print("\n✓ Compilation complete!")
    print("\nFiles generated:")
    print("- build/ArbitrageBotV2.bin (Bytecode)")
    print("- build/ArbitrageBotV2.abi (ABI)")
    print("- build/deployment_info.json (Deployment Info)")
    
    print("\nNext steps:")
    print("1. Review the generated files")
    print("2. Deploy using Remix or Hardhat")
    print("3. Verify contract on Etherscan")
    print("4. Set up monitoring")


if __name__ == '__main__':
    main()
