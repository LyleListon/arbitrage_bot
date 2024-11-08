import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv


class KeyManager:
    def __init__(self):
        load_dotenv()
        self.encryption_key = os.getenv('ENCRYPTION_KEY')
        if not self.encryption_key or len(self.encryption_key) != 44:
            self.generate_new_key()
        self.fernet = Fernet(self.encryption_key)

    def generate_new_key(self):
        new_key = Fernet.generate_key().decode()
        os.environ['ENCRYPTION_KEY'] = new_key
        with open('.env', 'a') as env_file:
            env_file.write(f"\nENCRYPTION_KEY={new_key}\n")
        self.encryption_key = new_key

    def encrypt_key(self, private_key: str) -> str:
        return self.fernet.encrypt(private_key.encode()).decode()

    def decrypt_key(self, encrypted_key: str) -> str:
        return self.fernet.decrypt(encrypted_key.encode()).decode()

    def store_key(self, key_name: str, private_key: str):
        encrypted_key = self.encrypt_key(private_key)
        os.environ[key_name] = encrypted_key
        with open('.env', 'a') as env_file:
            env_file.write(f"{key_name}={encrypted_key}\n")

    def get_key(self, key_name: str) -> str:
        encrypted_key = os.getenv(key_name)
        if not encrypted_key:
            raise ValueError(f"Key '{key_name}' not found")
        return self.decrypt_key(encrypted_key)


# Usage example:
# key_manager = KeyManager()
# key_manager.store_key('ETH_PRIVATE_KEY', 'your_private_key_here')
# private_key = key_manager.get_key('ETH_PRIVATE_KEY')
