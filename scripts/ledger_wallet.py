from web3 import Web3
from typing import Optional
from eth_utils import keccak, to_bytes
import hid


class LedgerWallet:
    # Ethereum App configuration
    CLA = 0xE0
    INS_GET_PUBLIC_KEY = 0x02
    INS_SIGN_TX = 0x04
    P1_FIRST = 0x00
    P1_MORE = 0x80
    P2_LAST = 0x00
    P2_MORE = 0x80
    CHUNK_SIZE = 64  # Max size for transaction data chunks
    
    # BIP32 path: m/44'/60'/0'/0/0
    PATH = bytes([
        0x05,  # Number of path components
        0x80, 0x00, 0x00, 0x2c,  # 44'
        0x80, 0x00, 0x00, 0x3c,  # 60'
        0x80, 0x00, 0x00, 0x00,  # 0'
        0x00, 0x00, 0x00, 0x00,  # 0
        0x00, 0x00, 0x00, 0x00   # 0
    ])

    def __init__(self):
        """Initialize connection to Ledger device."""
        print("Connecting to Ledger...")
        try:
            # Find Ledger device
            devices = hid.enumerate(0x2c97, 0x5011)  # Ledger Nano S Plus
            if not devices:
                raise Exception("No Ledger device found")
            
            # Find device with correct usage page
            device_info = None
            for d in devices:
                if d.get('usage_page', 0) == 0xffa0:
                    device_info = d
                    break
            
            if not device_info:
                raise Exception(
                    "No Ledger device found with correct usage page"
                )
            
            # Open device
            self.device = hid.device()
            self.device.open_path(device_info['path'])
            self.device.set_nonblocking(False)
            
            print("Connected to Ledger device")
            print(f"Manufacturer: {self.device.get_manufacturer_string()}")
            print(f"Product: {self.device.get_product_string()}")
            
            print("\nGetting Ethereum address...")
            self.address = self._get_address()
            print(f"Address: {self.address}")
            
        except Exception as e:
            raise Exception(f"Failed to connect to Ledger: {str(e)}")

    def _exchange(self, apdu_command: bytes) -> bytes:
        """Send command and receive response."""
        # Send command with channel ID
        data = bytes([
            0x00,  # Report ID
            0x01, 0x01,  # Channel ID
            0x05,  # Command tag
            0x00,  # Packet sequence
        ]) + apdu_command
        data = data.ljust(65, b'\x00')  # Pad to 65 bytes
        
        print(f"Sending: {data.hex()}")
        self.device.write(data)
        
        # Read response
        response = bytes(self.device.read(65))
        if not response:
            raise Exception("No response from device")
        print(f"Received: {response.hex()}")
        
        return response[5:]  # Skip header

    def _get_address(self) -> str:
        """Get Ethereum address from Ledger."""
        try:
            print("Sending get address command...")
            
            # Construct APDU command
            apdu = bytes([
                self.CLA,
                self.INS_GET_PUBLIC_KEY,
                0x00,  # P1: Return address
                0x00,  # P2: No chain code
                len(self.PATH)  # Lc: data length
            ]) + self.PATH
            
            response = self._exchange(apdu)
            
            # Extract public key (65 bytes for uncompressed key)
            pub_key = response[1:66]
            
            # Derive Ethereum address from public key
            # Remove first byte (0x04 which indicates uncompressed key)
            pub_key_hash = keccak(pub_key[1:])
            # Take last 20 bytes
            address = Web3.to_checksum_address(
                '0x' + pub_key_hash[-20:].hex()
            )
            return address
            
        except Exception as e:
            msg = f"Failed to get address from Ledger: {str(e)}"
            raise Exception(msg)

    def sign_transaction(self, transaction_dict: dict) -> dict:
        """Sign an Ethereum transaction using Ledger."""
        try:
            print("\nPreparing transaction for signing...")
            unsigned_tx = self._prepare_transaction(transaction_dict)
            
            print("Sending transaction to Ledger...")
            print("Please check your Ledger device...")
            
            # Construct APDU command
            apdu = bytes([
                self.CLA,
                self.INS_SIGN_TX,
                self.P1_FIRST,
                0x00,  # P2
                len(unsigned_tx)  # Lc: data length
            ]) + unsigned_tx
            
            response = self._exchange(apdu)
            
            if not response:
                raise Exception("No response from device")
            
            # Extract signature
            v = response[0]
            r = int.from_bytes(response[1:33], byteorder='big')
            s = int.from_bytes(response[33:65], byteorder='big')
            
            # Return signed transaction components
            return {
                'v': v,
                'r': r,
                's': s
            }
            
        except Exception as e:
            msg = f"Failed to sign transaction: {str(e)}"
            raise Exception(msg)

    def _prepare_transaction(self, transaction: dict) -> bytes:
        """Prepare transaction data for Ledger signing."""
        try:
            # Convert values to bytes with proper padding
            nonce = transaction['nonce'].to_bytes(4, 'big')
            gas_price = transaction['gasPrice'].to_bytes(8, 'big')
            gas = transaction['gas'].to_bytes(4, 'big')
            
            # Handle 'to' address
            if transaction.get('to'):
                to_addr = to_bytes(hexstr=transaction['to'])
            else:
                to_addr = b''
            
            # Handle value
            value = transaction.get('value', 0)
            value_bytes = value.to_bytes(8, 'big')
            
            # Handle data
            data = transaction.get('data', b'')
            if isinstance(data, str):
                if data.startswith('0x'):
                    data = to_bytes(hexstr=data)
                else:
                    data = to_bytes(text=data)
            
            # Combine all fields
            return b''.join([
                nonce,
                gas_price,
                gas,
                to_addr,
                value_bytes,
                data
            ])
            
        except Exception as e:
            raise ValueError(f"Failed to prepare transaction: {str(e)}")

    def get_balance(
        self,
        w3: Web3,
        token_address: Optional[str] = None
    ) -> int:
        """Get balance of ETH or ERC20 token."""
        if token_address:
            # Get ERC20 token balance
            contract = w3.eth.contract(
                address=token_address,
                abi=[{
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }]
            )
            return contract.functions.balanceOf(self.address).call()
        else:
            # Get ETH balance
            return w3.eth.get_balance(self.address)

    def close(self):
        """Close connection to Ledger device."""
        if hasattr(self, 'device'):
            self.device.close()
