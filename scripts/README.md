# Verification and Monitoring Scripts

## Overview
These scripts help ensure safe deployment and operation on mainnet.

### verify_mainnet_config.py
Verifies all mainnet configuration settings:
- Network connection
- Contract addresses
- Price feed health
- Safety parameters
- Exchange configuration
- Token balances
- Gas estimates

Usage:
```bash
# Run verification
python scripts/verify_mainnet_config.py

# Check specific components
python scripts/verify_mainnet_config.py --check network
python scripts/verify_mainnet_config.py --check contracts
python scripts/verify_mainnet_config.py --check price-feeds
```

### monitor_mainnet.py
Real-time monitoring of mainnet health:
- Network status
- Gas prices
- Block times
- Price feed health
- DEX liquidity
- Trading conditions

Usage:
```bash
# Start monitoring
python scripts/monitor_mainnet.py

# With custom interval
python scripts/monitor_mainnet.py --interval 30

# With alerts
python scripts/monitor_mainnet.py --alerts telegram
```

## Important Notes
1. Run ALL verifications before deployment
2. Monitor script outputs carefully
3. Address ANY warnings or errors
4. Document verification results
5. Keep scripts updated with new checks

## Adding New Checks
When adding new contracts or features:
1. Add corresponding verification checks
2. Update monitoring parameters
3. Test thoroughly
4. Monitor results
