from ledgerblue.comm import getDongle
import struct
from eth_utils import to_checksum_address, keccak
import time


def format_bip32_path():
    """Format BIP32 path for Ethereum address (m/44'/60'/0'/0/0)."""
    path = [
        0x8000002C,  # 44'
        0x8000003C,  # 60'
        0x80000000,  # 0'
        0x00000000,  # 0
        0x00000000   # 0
    ]
    return b"".join(struct.pack(">I", i) for i in path)


def parse_response(response):
    """Parse the response from Ledger."""
    try:
        # Response format:
        # [pub_key_len(1)] [pub_key(var)] [addr_len(1)] [addr(var)] [status(2)]
        
        # Get public key length (first byte)
        pub_key_len = response[0]
        # Extract public key
        pub_key = response[1:pub_key_len+1]
        
        # Get address from response
        addr_start = pub_key_len + 2  # +1 for pub_key, +1 for addr_len
        addr_len = response[pub_key_len + 1]
        addr = response[addr_start:addr_start + addr_len].decode('ascii')
        
        # Last two bytes are status code
        status = response[-2:].hex()
        
        return {
            'public_key': pub_key.hex(),
            'address': addr,
            'status': status
        }
    except Exception:
        # Fallback to deriving address from public key
        pub_key = response[1:66]
        pub_key_hash = keccak(pub_key[1:])
        address = to_checksum_address('0x' + pub_key_hash[-20:].hex())
        
        return {
            'public_key': pub_key.hex(),
            'address': address,
            'status': response[-2:].hex()
        }


def test_ledger():
    """Test communication with Ledger using ledgerblue."""
    print("\nChecking Ledger status...")
    print("1. Please make sure your Ledger is connected")
    print("2. Enter your PIN to unlock if needed")
    print("3. Open the Ethereum app")
    print("4. Wait for 'Application is ready' on the Ledger screen")
    print("\nPress Enter when ready...")
    input()
    
    print("\nConnecting to Ledger...")
    
    try:
        # Get dongle object
        dongle = getDongle(debug=True)
        print("✅ Connected to Ledger device")
        
        # Give the app time to fully initialize
        print("Waiting for Ethereum app to be ready...")
        time.sleep(2)
        
        # Format get Ethereum address command
        bip32_path = format_bip32_path()
        apdu = bytes([
            0xE0,        # CLA
            0x02,        # INS: GET_PUBLIC_KEY
            0x00,        # P1: Return address
            0x00,        # P2: No chain code
            0x15,        # Data length (21 bytes)
            0x05,        # Number of BIP32 derivations
        ]) + bip32_path
        
        print("\nSending get address command...")
        print("⚠️  Please check your Ledger device - it may ask for confirmation")
        
        # Send command to device
        response = dongle.exchange(apdu)
        result = parse_response(response)
        
        print("\nResponse received:")
        print(f"Public Key: {result['public_key']}")
        print(f"Address: {result['address']}")
        print(f"Status: {result['status']}")
        
        if result['status'] == '9000':
            print("\n✅ Successfully retrieved Ethereum address!")
        else:
            print("\n⚠️  Note: Got address but with unexpected status code")
            print("Expected: 9000")
            print(f"Received: {result['status']}")
            print("\nThe address should still be correct:")
            print(f"👉 {result['address']}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure the Ledger is unlocked")
        print("2. Open the Ethereum app")
        print("3. Wait for 'Application is ready'")
        print("4. Try running the script again")
    finally:
        if 'dongle' in locals():
            dongle.close()


if __name__ == "__main__":
    print("Ledger Blue Communication Test")
    print("-----------------------------")
    print("Prerequisites:")
    print("1. Ledger is connected via USB")
    print("2. Ledger is unlocked")
    print("3. Ethereum app is open")
    print("4. Blind signing is enabled")
    print()
    
    test_ledger()
