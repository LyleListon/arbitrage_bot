import ctypes
from ctypes import wintypes
import time

# Windows API constants
DIGCF_PRESENT = 0x2
DIGCF_DEVICEINTERFACE = 0x10
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
OPEN_EXISTING = 0x3

# Ledger constants
LEDGER_VENDOR_ID = 0x2c97
LEDGER_PRODUCT_ID = 0x5011

# Load DLLs
hid = ctypes.WinDLL("hid.dll")
setupapi = ctypes.WinDLL("setupapi.dll")
kernel32 = ctypes.WinDLL("kernel32.dll")


def get_hid_device_path():
    """Get HID device path for Ledger."""
    print("Searching for Ledger device...")
    
    # Create GUID for HID class
    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", wintypes.DWORD),
            ("Data2", wintypes.WORD),
            ("Data3", wintypes.WORD),
            ("Data4", ctypes.c_byte * 8)
        ]
    
    HidGuid = GUID()
    hid.HidD_GetHidGuid(ctypes.byref(HidGuid))
    
    # Get device info set
    hDevInfo = setupapi.SetupDiGetClassDevsW(
        ctypes.byref(HidGuid),
        None,
        None,
        DIGCF_PRESENT | DIGCF_DEVICEINTERFACE
    )
    
    if hDevInfo == -1:
        print("Failed to get device info set")
        return None
    
    try:
        # Device interface data structure
        class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("InterfaceClassGuid", GUID),
                ("Flags", wintypes.DWORD),
                ("Reserved", ctypes.POINTER(wintypes.ULONG))
            ]
        
        # Enumerate devices
        DeviceInterfaceData = SP_DEVICE_INTERFACE_DATA()
        DeviceInterfaceData.cbSize = ctypes.sizeof(SP_DEVICE_INTERFACE_DATA)
        device_index = 0
        
        while setupapi.SetupDiEnumDeviceInterfaces(
            hDevInfo,
            None,
            ctypes.byref(HidGuid),
            device_index,
            ctypes.byref(DeviceInterfaceData)
        ):
            # Get required buffer size
            RequiredSize = wintypes.DWORD()
            setupapi.SetupDiGetDeviceInterfaceDetailW(
                hDevInfo,
                ctypes.byref(DeviceInterfaceData),
                None,
                0,
                ctypes.byref(RequiredSize),
                None
            )
            
            # Create buffer
            class SP_DEVICE_INTERFACE_DETAIL_DATA(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.DWORD),
                    ("DevicePath", ctypes.c_wchar * RequiredSize.value)
                ]
            
            DetailData = SP_DEVICE_INTERFACE_DETAIL_DATA()
            DetailData.cbSize = 8  # Size of the cbSize member
            
            # Get device path
            if setupapi.SetupDiGetDeviceInterfaceDetailW(
                hDevInfo,
                ctypes.byref(DeviceInterfaceData),
                ctypes.byref(DetailData),
                RequiredSize,
                None,
                None
            ):
                # Try to open device
                handle = kernel32.CreateFileW(
                    DetailData.DevicePath,
                    GENERIC_READ | GENERIC_WRITE,
                    FILE_SHARE_READ | FILE_SHARE_WRITE,
                    None,
                    OPEN_EXISTING,
                    0,
                    None
                )
                
                if handle != -1:
                    # Check if it's a Ledger device
                    class HIDD_ATTRIBUTES(ctypes.Structure):
                        _fields_ = [
                            ("Size", wintypes.ULONG),
                            ("VendorID", wintypes.USHORT),
                            ("ProductID", wintypes.USHORT),
                            ("VersionNumber", wintypes.USHORT)
                        ]
                    
                    attrib = HIDD_ATTRIBUTES()
                    attrib.Size = ctypes.sizeof(HIDD_ATTRIBUTES)
                    
                    if hid.HidD_GetAttributes(handle, ctypes.byref(attrib)):
                        if (attrib.VendorID == LEDGER_VENDOR_ID and
                            attrib.ProductID == LEDGER_PRODUCT_ID):
                            print("\nFound Ledger Nano S Plus!")
                            kernel32.CloseHandle(handle)
                            return DetailData.DevicePath
                    
                    kernel32.CloseHandle(handle)
            
            device_index += 1
        
        print("\nNo Ledger device found")
        return None
        
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(hDevInfo)


def test_ledger_communication(device_path):
    """Test communication with Ledger device."""
    if not device_path:
        return
    
    print(f"\nOpening device: {device_path}")
    
    handle = kernel32.CreateFileW(
        device_path,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    
    if handle == -1:
        print("Failed to open device")
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
        
        # Send command
        print("Sending command to get public key...")
        bytes_written = wintypes.DWORD()
        if kernel32.WriteFile(
            handle,
            apdu,
            len(apdu),
            ctypes.byref(bytes_written),
            None
        ):
            print(f"Sent {bytes_written.value} bytes")
            
            # Wait for response
            print("Waiting for response...")
            time.sleep(1)  # Give device time to process
            
            # Read response
            response = ctypes.create_string_buffer(64)
            bytes_read = wintypes.DWORD()
            if kernel32.ReadFile(
                handle,
                response,
                64,
                ctypes.byref(bytes_read),
                None
            ):
                print(f"Received {bytes_read.value} bytes")
                print(f"Response: {bytes(response.raw)[:bytes_read.value].hex()}")
            else:
                print("Failed to read response")
        else:
            print("Failed to send command")
            
    finally:
        kernel32.CloseHandle(handle)


def main():
    print("Ledger Direct Communication Test")
    print("-------------------------------")
    print("Prerequisites:")
    print("1. Ledger device is connected via USB")
    print("2. Ledger is unlocked")
    print("3. Ethereum app is open")
    print("4. Blind signing is enabled")
    
    device_path = get_hid_device_path()
    if device_path:
        test_ledger_communication(device_path)
    else:
        print("\nTroubleshooting steps:")
        print("1. Check USB connection")
        print("2. Unlock your Ledger")
        print("3. Open the Ethereum app")
        print("4. Try a different USB port")


if __name__ == "__main__":
    main()
