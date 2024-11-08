from web3 import Web3
import time


# List of Sepolia RPC endpoints to test
RPC_ENDPOINTS = [
    "https://eth-sepolia.g.alchemy.com/v2/demo",
    "https://rpc.sepolia.org",
    "https://rpc2.sepolia.org",
    "https://sepolia.infura.io/v3/9aa3d95b3bc440fa88ea12eaa4456161",
    "https://ethereum-sepolia.publicnode.com",
    "https://sepolia.gateway.tenderly.co",
]


def test_rpc(url):
    """Test RPC endpoint and return response time if successful."""
    try:
        start_time = time.time()
        w3 = Web3(Web3.HTTPProvider(url))
        
        # Test basic RPC calls
        chain_id = w3.eth.chain_id  # Should be 11155111 for Sepolia
        block_number = w3.eth.block_number
        is_connected = w3.is_connected()
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return {
            'success': True,
            'chain_id': chain_id,
            'block': block_number,
            'connected': is_connected,
            'response_time': response_time
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    print("Testing Sepolia RPC endpoints...\n")
    
    working_endpoints = []
    
    for url in RPC_ENDPOINTS:
        print(f"Testing {url}")
        result = test_rpc(url)
        
        if result['success']:
            print("✅ SUCCESS:")
            print(f"   Chain ID: {result['chain_id']}")
            print(f"   Block: {result['block']}")
            print(f"   Connected: {result['connected']}")
            print(f"   Response Time: {result['response_time']:.2f}s")
            working_endpoints.append((url, result['response_time']))
        else:
            print(f"❌ FAILED: {result['error']}")
        print()
    
    if working_endpoints:
        print("\nWorking endpoints (sorted by response time):")
        for url, response_time in sorted(working_endpoints, key=lambda x: x[1]):
            print(f"{response_time:.2f}s - {url}")
    else:
        print("\nNo working endpoints found!")


if __name__ == "__main__":
    main()
