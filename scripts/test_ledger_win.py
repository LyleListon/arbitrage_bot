from pywinusb import hid
import time


def raw_handler(data):
    """Handle raw data from device."""
    print(f"Received: {data}")


def find_ledger_device():
    """Find and connect to Ledger device."""
    print("Searching for Ledger device...")
    
    # Ledger Nano S/X vendor ID
    LEDGER_VENDOR_ID = 0x2c97
    
    # Find all HID devices
    all_hids = hid.find_all_hid_devices()
    print(f"\nFound {len(all_hids)} HID devices")
    
    # Find Ledger devices
    ledger_devices = [
        device for device in all_hids
        if device.vendor_id == LEDGER_VENDOR_ID
    ]
    
    if not ledger_devices:
        print("\n❌ No Ledger devices found")
        return None
    
    print(f"\nFound {len(ledger_devices)} Ledger devices:")
    for idx, device in enumerate(ledger_devices, 1):
        print(f"\nDevice #{idx}:")
        print(f"Product ID: {device.product_id:04x}")
        print(f"Vendor ID: {device.vendor_id:04x}")
        print(f"Serial Number: {device.serial_number}")
        print(f"Product Name: {device.product_name}")
        print(f"Manufacturer: {device.vendor_name}")
    
    # Try to open first Ledger device
    device = ledger_devices[0]
    try:
        if device.open():
            print("\n✅ Successfully opened device")
            
            # Set up data handler
            device.set_raw_data_handler(raw_handler)
            
            # Get device reports
            reports = device.find_output_reports()
            if reports:
                print(f"Found {len(reports)} output reports")
                for report in reports:
                    print(f"Report ID: {report.report_id}")
            else:
                print("No output reports found")
            
            return device
    except Exception as e:
        print(f"\n❌ Failed to open device: {str(e)}")
        return None


def test_ledger_communication(device):
    """Test communication with Ledger device."""
    if not device:
        return
    
    try:
        print("\nTesting communication...")
        
        # Get public key APDU command
        apdu = bytes([
            0xE0,  # CLA
            0x02,  # INS (get public key)
            0x00,  # P1
            0x00,  # P2
            0x15,  # Length
            # BIP32 path: m/44'/60'/0'/0/0
            0x05,  # Number of path components
            0x80, 0x00, 0x00, 0x2c,  # 44'
            0x80, 0x00, 0x00, 0x3c,  # 60'
            0x80, 0x00, 0x00, 0x00,  # 0'
            0x00, 0x00, 0x00, 0x00,  # 0
            0x00, 0x00, 0x00, 0x00   # 0
        ])
        
        # Find first output report
        report = device.find_output_reports()[0]
        
        # Send command
        print("Sending command to get public key...")
        report.set_raw_data(apdu)
        report.send()
        
        # Wait for response
        print("Waiting for response...")
        time.sleep(2)
        
    except Exception as e:
        print(f"\n❌ Communication error: {str(e)}")
    finally:
        device.close()


def main():
    print("Ledger Communication Test")
    print("------------------------")
    print("Prerequisites:")
    print("1. Ledger device is connected via USB")
    print("2. Ledger is unlocked")
    print("3. Ethereum app is open")
    print("4. Blind signing is enabled")
    
    device = find_ledger_device()
    if device:
        test_ledger_communication(device)
    else:
        print("\nTroubleshooting steps:")
        print("1. Check USB connection")
        print("2. Unlock your Ledger")
        print("3. Open the Ethereum app")
        print("4. Try a different USB port")


if __name__ == "__main__":
    main()
