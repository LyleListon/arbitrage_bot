import hid

def find_ledger_interfaces():
    """List all available Ledger device interfaces."""
    print("Searching for Ledger devices...")
    
    # Ledger vendor and product IDs
    LEDGER_VENDOR_ID = 0x2c97
    LEDGER_NANO_S_ID = 0x1011
    LEDGER_NANO_X_ID = 0x4011
    LEDGER_NANO_S_PLUS_ID = 0x5011
    
    # List all HID devices
    devices = hid.enumerate()
    print(f"\nFound {len(devices)} HID devices")
    
    # Filter Ledger devices
    ledger_devices = []
    for device in devices:
        if device['vendor_id'] == LEDGER_VENDOR_ID:
            if device['product_id'] in [
                LEDGER_NANO_S_ID,
                LEDGER_NANO_X_ID,
                LEDGER_NANO_S_PLUS_ID
            ]:
                ledger_devices.append(device)
    
    print(f"\nFound {len(ledger_devices)} Ledger devices:")
    
    # Try to open each interface
    for idx, device_info in enumerate(ledger_devices, 1):
        print(f"\nDevice #{idx}:")
        print(f"Product ID: {device_info['product_id']:04x}")
        print(f"Interface: {device_info.get('interface_number', 'Not specified')}")
        print(f"Usage Page: {device_info.get('usage_page', 'Not specified'):04x}")
        print(f"Path: {device_info['path']}")
        
        try:
            device = hid.device()
            device.open_path(device_info['path'])
            print("✅ Successfully opened connection")
            print(f"Manufacturer: {device.get_manufacturer_string()}")
            print(f"Product: {device.get_product_string()}")
            device.close()
        except Exception as e:
            print(f"❌ Failed to open: {str(e)}")

if __name__ == "__main__":
    find_ledger_interfaces()
    print("\nPlease check which interface successfully opened")
    print("and make note of its Usage Page and Interface number.")
