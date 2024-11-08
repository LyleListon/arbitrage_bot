import hid
import struct


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


def send_apdu(device, cla, ins, p1, p2, data=b""):
    """Send APDU command using HID protocol."""
    if len(data) > 250:
        raise ValueError("Data too long")
    
    # Construct APDU
    apdu = bytes([cla, ins, p1, p2, len(data)]) + data
    
    # HID Report structure:
    # [0]: Report ID
    # [1:3]: Channel ID (0x0301 for HID)
    # [3]: Command Tag (0x05)
    # [4]: Packet Sequence Index
    # [5:]: Packet Data
    data = bytes([
        0x00,  # Report ID
        0x03, 0x01,  # Channel ID
        0x05,  # Command tag
        0x00,  # Packet sequence
    ]) + apdu
    
    # Pad to 64 bytes
    data = data.ljust(64, b'\x00')
    
    print(f"Sending: {data.hex()}")
    device.write(data)
    
    # Read response with retries
    for _ in range(3):  # Try 3 times
        response = device.read(64, timeout_ms=1000)
        if response:
            print(f"Received: {bytes(response).hex()}")
            return bytes(response)
    
    raise TimeoutError("No response from device")


def test_ledger():
    """Test communication with Ledger."""
    print("Looking for Ledger device...")
    
    # List all HID devices
    devices = hid.enumerate(0x2c97, 0x5011)
    if not devices:
        print("No Ledger devices found")
        return
    
    print(f"\nFound {len(devices)} interfaces:")
    for dev in devices:
        print(f"Interface {dev.get('interface_number', 'N/A')}")
        print(f"Usage Page: {dev.get('usage_page', 'N/A'):x}")
    
    try:
        # Open Ledger device
        device = hid.device()
        device.open(0x2c97, 0x5011)  # Ledger Nano S Plus
        device.set_nonblocking(False)
        
        print(f"\nConnected to: {device.get_product_string()}")
        
        # Get Ethereum address command
        bip32_path = format_bip32_path()
        data = bytes([0x05]) + bip32_path  # 0x05 = path length
        
        print("\nSending get address command...")
        print("Please check your Ledger device...")
        
        response = send_apdu(
            device,
            cla=0xE0,    # Ethereum app CLA
            ins=0x02,    # GET_PUBLIC_KEY instruction
            p1=0x00,     # Return address
            p2=0x00,     # No chain code
            data=data    # BIP32 path
        )
        
        print("\nCommand completed")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        device.close()


if __name__ == "__main__":
    print("Ledger Ethereum Address Test")
    print("---------------------------")
    print("Prerequisites:")
    print("1. Ledger is connected via USB")
    print("2. Ledger is unlocked")
    print("3. Ethereum app is open")
    print("4. Blind signing is enabled")
    print()
    
    test_ledger()
