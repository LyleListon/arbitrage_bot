import json
import os
from typing import Dict, Any
from pathlib import Path

class ConfigLoader:
    """
    Configuration loader that handles merging template, network-specific,
    and local configurations.
    """
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.template_path = self.config_dir / "template.json"
        self.networks_dir = self.config_dir / "networks"
        self.local_path = self.config_dir / "local.json"

    def load_json(self, path: Path) -> Dict[str, Any]:
        """Load a JSON file safely."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found: {path}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in config file: {path}")
            return {}

    def deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with override taking precedence.
        """
        merged = base.copy()
        
        for key, value in override.items():
            if (
                key in merged and 
                isinstance(merged[key], dict) and 
                isinstance(value, dict)
            ):
                merged[key] = self.deep_merge(merged[key], value)
            else:
                merged[key] = value
                
        return merged

    def load_config(self, network: str = None) -> Dict[str, Any]:
        """
        Load configuration for specified network, merging template,
        network-specific, and local configurations.
        """
        # Load base template
        config = self.load_json(self.template_path)
        
        # Load network-specific config if specified
        if network:
            network_path = self.networks_dir / f"{network}.json"
            network_config = self.load_json(network_path)
            config = self.deep_merge(config, network_config)
        
        # Load local overrides if they exist
        local_config = self.load_json(self.local_path)
        config = self.deep_merge(config, local_config)
        
        return config

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure and required fields.
        """
        required_fields = [
            "network",
            "base_rpc_url",
            "account_address",
            "trading_params",
            "tokens",
            "dexes"
        ]
        
        for field in required_fields:
            if field not in config:
                print(f"Error: Missing required field: {field}")
                return False
                
        if not config["tokens"]:
            print("Error: No tokens configured")
            return False
            
        if not config["dexes"]:
            print("Error: No DEXes configured")
            return False
            
        return True

    def get_networks(self) -> list:
        """
        Get list of available network configurations.
        """
        networks = []
        if self.networks_dir.exists():
            for file in self.networks_dir.glob("*.json"):
                networks.append(file.stem)
        return networks

    def create_local_template(self):
        """
        Create a template for local.json with sensitive fields.
        """
        template = {
            "private_key": "YOUR_PRIVATE_KEY",
            "base_rpc_url": "YOUR_RPC_URL",
            "account_address": "YOUR_WALLET_ADDRESS"
        }
        
        local_template_path = self.config_dir / "local.template.json"
        with open(local_template_path, 'w') as f:
            json.dump(template, f, indent=4)
            
        print(f"Created local config template at: {local_template_path}")
        print("Fill in your private information and save as local.json")

def load_network_config(network: str) -> Dict[str, Any]:
    """
    Convenience function to load configuration for a specific network.
    """
    loader = ConfigLoader()
    config = loader.load_config(network)
    
    if not loader.validate_config(config):
        raise ValueError(f"Invalid configuration for network: {network}")
        
    return config

if __name__ == "__main__":
    import sys
    
    loader = ConfigLoader()
    
    if len(sys.argv) > 1:
        network = sys.argv[1]
        try:
            config = load_network_config(network)
            print(f"Loaded configuration for network: {network}")
            print(json.dumps(config, indent=2))
        except ValueError as e:
            print(f"Error: {e}")
    else:
        print("Available networks:", loader.get_networks())
        print("Usage: python config_loader.py [network]")
        loader.create_local_template()
