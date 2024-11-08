import subprocess
import sys
import json

def test_ledger_connection():
    """Test Ledger connection using ledger-live CLI."""
    print("Testing Ledger connection...")
    print("\nPrerequisites:")
    print("1. Ledger device is connected via USB")
    print("2. Ledger device is unlocked")
    print("3. Ethereum app is open")
    print("4. Blind signing is enabled")
    
    try:
        # Try to get Ethereum address using ledger-live
        print("\nAttempting to get Ethereum address...")
        result = subprocess.run(
            ["ledger-live", "getAddress", "--currency", "ethereum"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            try:
                address_data = json.loads(result.stdout)
                print(f"\n✅ Successfully connected to Ledger!")
                print(f"Ethereum Address: {address_data['address']}")
                return True
            except json.JSONDecodeError:
                print("\n❌ Error parsing Ledger response")
                print(f"Output: {result.stdout}")
                return False
        else:
            print("\n❌ Failed to connect to Ledger")
            print(f"Error: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("\n❌ ledger-live CLI not found")
        print("Please install Ledger Live Desktop application")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    if not test_ledger_connection():
        print("\nTroubleshooting steps:")
        print("1. Ensure Ledger Live is installed")
        print("2. Make sure your Ledger is connected and unlocked")
        print("3. Open the Ethereum app on your Ledger")
        print("4. Enable Blind signing in the Ethereum app settings")
        print("5. Try disconnecting and reconnecting your Ledger")
        sys.exit(1)
