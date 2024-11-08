# Configuration Setup Guide

## Quick Start

1. Copy the local template:
   ```bash
   cp configs/local.template.json configs/local.json
   ```

2. Edit configs/local.json with your private information:
   - Add your private key
   - Add your wallet address
   - Add your RPC URL

3. Load configuration in your code:
   ```python
   from configs.config_loader import load_network_config
   
   # Load Sepolia configuration
   config = load_network_config("sepolia")
   ```

## Configuration Files

### Template (template.json)
- Base configuration structure
- Default values for all settings
- Reference for configuration structure

### Network Configs (networks/*.json)
- Network-specific settings
- Contract addresses
- Network parameters
- DEX configurations

### Local Config (local.json)
- Private keys
- RPC URLs
- Personal wallet addresses
- Never committed to git

## Using the Config Loader

### List Available Networks
```python
from configs.config_loader import ConfigLoader

loader = ConfigLoader()
networks = loader.get_networks()
print("Available networks:", networks)
```

### Load Network Configuration
```python
from configs.config_loader import load_network_config

# Load specific network config
config = load_network_config("sepolia")

# Access configuration
rpc_url = config["base_rpc_url"]
tokens = config["tokens"]
dexes = config["dexes"]
```

### Validate Configuration
```python
from configs.config_loader import ConfigLoader

loader = ConfigLoader()
config = loader.load_config("sepolia")

if loader.validate_config(config):
    print("Configuration is valid")
else:
    print("Configuration is invalid")
```

## Security Notes

1. Never commit local.json to git
2. Keep private keys secure
3. Use environment variables when possible
4. Regularly rotate testing keys

## Configuration Structure

### Trading Parameters
```json
{
    "trading_params": {
        "update_interval": 10,
        "min_spread": 100,
        "min_profit": "0.01",
        "gas_limit": 500000,
        "slippage_tolerance": 50,
        "max_trade_size": "1.0"
    }
}
```

### Token Configuration
```json
{
    "tokens": {
        "WETH": "0x...",
        "USDC": "0x...",
        "USDT": "0x...",
        "DAI": "0x..."
    }
}
```

### DEX Configuration
```json
{
    "dexes": {
        "UniswapV3": {
            "router": "0x...",
            "factory": "0x...",
            "quoter": "0x...",
            "type": "UniswapV3",
            "gas_estimate": 180000
        }
    }
}
```

## Troubleshooting

1. Missing Configuration
   - Ensure all required files exist
   - Check file permissions
   - Verify JSON syntax

2. Invalid Configuration
   - Run validation check
   - Check required fields
   - Verify network settings

3. Loading Issues
   - Check file paths
   - Verify JSON format
   - Check network name spelling

## Migration from Old Config

1. Backup existing configs
2. Copy relevant values to new structure
3. Validate new configuration
4. Update code to use new loader

## Support

For issues or questions:
1. Check configuration documentation
2. Verify file structure
3. Run validation checks
4. Review error messages
