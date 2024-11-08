# Configuration Structure

## Overview
The project uses a hierarchical configuration system with:
1. Base template (template.json)
2. Network-specific overrides (networks/{network}.json)
3. Local overrides (local.json) - gitignored for private keys

## Configuration Parameters

### Network Configuration
- `base_rpc_url`: RPC endpoint for the network
- `account_address`: Wallet address for transactions
- `private_key`: Private key (only in local.json)

### Trading Parameters
- `update_interval`: Price check interval (seconds)
- `min_spread`: Minimum price spread for arbitrage (basis points)
- `min_profit`: Minimum profit threshold in ETH
- `gas_limit`: Maximum gas for transactions
- `slippage_tolerance`: Maximum allowed slippage (basis points)
- `max_trade_size`: Maximum trade size in ETH

### Token Configuration
- `tokens`: Map of token symbols to addresses
  - WETH
  - USDC
  - USDT
  - DAI
  etc.

### DEX Configuration
Each DEX entry contains:
- `router`: Router contract address
- `factory`: Factory contract address
- `type`: DEX type (UniswapV3, SushiSwap, etc.)
- `gas_estimate`: Estimated gas for trades
- `quoter`: (Optional) Quote contract address

## Usage

1. Start with template.json for new deployments
2. Create network-specific config in networks/
3. Create local.json for private keys
4. Use config.py to load and merge configurations

## Security Notes

- Never commit private keys
- Keep local.json in .gitignore
- Use environment variables for sensitive data
- Regularly rotate keys used in testing
