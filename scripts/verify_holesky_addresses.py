from web3 import Web3
from dotenv import load_dotenv
import os


def main():
    # Load Holesky configuration
    load_dotenv('.env.holesky')
    w3 = Web3(Web3.HTTPProvider(os.getenv('HOLESKY_RPC_URL')))
    print(f"Connected to Holesky: {w3.is_connected()}")
    
    # Official Holesky addresses (converted to checksum)
    addresses = {
        'WETH': Web3.to_checksum_address('0x94373a4919b3240d86ea41593d5eba789fef3848'),
        'USDC': Web3.to_checksum_address('0x9c4073e98da7d92427b550dc10e919dc54c3a61f'),
        'ETH/USD Feed': Web3.to_checksum_address('0x6d0f8f116a82224ab7dd132a6ef776c07d761562'),
        'USDC/USD Feed': Web3.to_checksum_address('0x31d3a7711a10c45d72649d51e1c8d74282702572')
    }
    
    print("\nVerifying Holesky Addresses:")
    print("-" * 50)
    
    for name, address in addresses.items():
        print(f"\n{name}:")
        print(f"Address: {address}")
        try:
            code = w3.eth.get_code(address)
            print(f"Contract exists: {'✓' if len(code) > 2 else '✗'}")
            print(f"Code size: {len(code)} bytes")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    print("\nCurrent Environment Values:")
    print("-" * 50)
    print(f"WETH_ADDRESS: {os.getenv('WETH_ADDRESS')}")
    print(f"USDC_ADDRESS: {os.getenv('USDC_ADDRESS')}")
    
    print("\nRecommended Updates:")
    print("-" * 50)
    print("Add these lines to your .env.holesky file:")
    print(f"WETH_ADDRESS={addresses['WETH']}")
    print(f"USDC_ADDRESS={addresses['USDC']}")
    print(f"ETH_USD_FEED={addresses['ETH/USD Feed']}")
    print(f"USDC_USD_FEED={addresses['USDC/USD Feed']}")
    
    # Create a backup of current .env.holesky
    try:
        with open('.env.holesky', 'r') as f:
            current_env = f.read()
        
        with open('.env.holesky.backup', 'w') as f:
            f.write(current_env)
        print("\n✓ Created backup at .env.holesky.backup")
        
        # Update .env.holesky with new addresses
        env_content = []
        for line in current_env.split('\n'):
            if line.startswith('WETH_ADDRESS='):
                env_content.append(f"WETH_ADDRESS={addresses['WETH']}")
            elif line.startswith('USDC_ADDRESS='):
                env_content.append(f"USDC_ADDRESS={addresses['USDC']}")
            elif line.startswith('ETH_USD_FEED='):
                env_content.append(f"ETH_USD_FEED={addresses['ETH/USD Feed']}")
            elif line.startswith('USDC_USD_FEED='):
                env_content.append(f"USDC_USD_FEED={addresses['USDC/USD Feed']}")
            else:
                env_content.append(line)
        
        # Add missing variables
        if not any(line.startswith('ETH_USD_FEED=') for line in env_content):
            env_content.append(f"ETH_USD_FEED={addresses['ETH/USD Feed']}")
        if not any(line.startswith('USDC_USD_FEED=') for line in env_content):
            env_content.append(f"USDC_USD_FEED={addresses['USDC/USD Feed']}")
        
        with open('.env.holesky', 'w') as f:
            f.write('\n'.join(env_content))
        print("✓ Updated .env.holesky with new addresses")
        
    except Exception as e:
        print(f"✗ Error updating .env.holesky: {str(e)}")


if __name__ == '__main__':
    main()
