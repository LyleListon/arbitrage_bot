# Arbitrage Bot

A sophisticated arbitrage bot for cryptocurrency trading, currently testing on Sepolia testnet with plans for mainnet deployment.

## Features

- Multi-DEX arbitrage opportunities detection
- Price feed integration with Chainlink
- Advanced monitoring and analytics dashboard
- Risk management system
- Automated trade execution
- Cross-chain capabilities

## Project Structure

- `/abi`: Smart contract ABIs
- `/contracts`: Solidity smart contracts
- `/dashboard`: Web-based monitoring dashboard
- `/scripts`: Deployment and utility scripts
- `/configs`: Configuration files
- `/docs`: Project documentation

## Setup

1. Clone the repository
2. Install dependencies:
```bash
npm install  # For JavaScript dependencies
pip install -r requirements.txt  # For Python dependencies
```

3. Configure environment:
- Copy `configs/local.template.json` to `configs/local.json`
- Update configuration with your settings

4. Deploy contracts:
```bash
npx hardhat run scripts/deploy.js --network sepolia
```

5. Start dashboard:
```bash
python run_dashboard.py
```

## Testing

```bash
npx hardhat test
python -m pytest test/
```

## Security

- All sensitive operations are protected
- Extensive input validation
- Rate limiting on API calls
- Risk management controls

## License

This project is licensed under the MIT License - see the LICENSE file for details.
