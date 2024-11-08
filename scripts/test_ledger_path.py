import ctypes
from ctypes import wintypes
import time

# Windows API constants
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x1
FILE_SHARE_WRITE = 0x2
OPEN_EXISTING = 0x3

# Load kernel32 for file operations
kernel32 = ctypes.WinDLL("kernel32.dll")

def test_ledger_communication():
    """Test communication with Ledger using known device path."""
    # Device path from previous test
    device_path = (
        "\\\\?\\HID#VID_2C97&PID_5011&MI_00"
        "#7&1325d663&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}"
    )
    
    print(f"Opening device: {device_path}")
    
    # Try to open device
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
        error = ctypes.get_last_error()
        print(f"Failed to open device. Error code: {error}")
        return
    
    try:
        print("\nDevice opened successfully!")
        print("Testing communication...")
        
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
        
        # Prepare HID report
        report = bytes([0x00]) + apdu  # Prepend report ID
        report = report.ljust(65, b'\x00')  # Pad to 65 bytes
        
        # Send command
        print("Sending command to get public key...")
        bytes_written = wintypes.DWORD()
        if kernel32.WriteFile(
            handle,
            report,
            len(report),
            ctypes.byref(bytes_written),
            None
        ):
            print(f"Sent {bytes_written.value} bytes")
            
            # Wait for response
            print("Waiting for response...")
            time.sleep(1)  # Give device time to process
            
            # Read response
            response = ctypes.create_string_buffer(65)  # 65 bytes for HID report
            bytes_read = wintypes.DWORD()
            if kernel32.ReadFile(
                handle,
                response,
                65,
                ctypes.byref(bytes_read),
                None
            ):
                print(f"Received {bytes_read.value} bytes")
                if bytes_read.value > 0:
                    # Skip report ID byte
                    data = bytes(response.raw)[1:bytes_read.value]
                    print(f"Response data: {data.hex()}")
                else:
                    print("No data received")
            else:
                error = ctypes.get_last_error()
                print(f"Failed to read response. Error code: {error}")
        else:
            error = ctypes.get_last_error()
            print(f"Failed to send command. Error code: {error}")
            
    finally:
        kernel32.CloseHandle(handle)


def main():
    print("Ledger Direct Communication Test (Using Device Path)")
    print("------------------------------------------------")
    print("Prerequisites:")
    print("1. Ledger device is connected via USB")
    print("2. Ledger is unlocked")
    print("3. Ethereum app is open")
    print("4. Blind signing is enabled")
    
    test_ledger_communication()


if __name__ == "__main__":
    main()
