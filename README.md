# Arbitrage Trading Bot

A sophisticated arbitrage trading bot for cryptocurrency markets, focusing on cross-DEX opportunities on the Base network.

## Features

- Real-time arbitrage opportunity detection
- Multi-DEX support (BaseSwap, Aerodrome)
- Advanced price analysis and monitoring
- Machine learning-based strategy optimization
- Comprehensive monitoring dashboard
- Risk management system

## System Components

- **Smart Contracts**: On-chain trading logic
- **Price Analysis**: Real-time market data processing
- **Trading Strategies**: Optimized trading algorithms
- **Monitoring Dashboard**: Real-time system visibility
- **Risk Management**: Trade validation and safety checks

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+
- Web3 provider
- Base network access

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd arbitrage_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

### Running the System

1. Start the main arbitrage bot:
```bash
python run.py
```

2. Launch the monitoring dashboard:
```bash
python -m dashboard.enhanced_app
```

3. Access the dashboard at http://localhost:5002

## Monitoring Dashboard

The system includes a comprehensive monitoring dashboard that provides:

- Real-time price monitoring across DEXes
- System performance metrics
- Trading opportunity analysis
- Health monitoring and alerts

For detailed information about the dashboard, see [Dashboard Guide](docs/DASHBOARD_GUIDE.md).

## Architecture

The system is built with a modular architecture that separates concerns and allows for easy maintenance and upgrades. For detailed architecture information, see [System Architecture](docs/SYSTEM_ARCHITECTURE.md).

## Configuration

- Network settings in `configs/networks/`
- Trading parameters in `config.yaml`
- Environment variables in `.env`

## Development

### Project Structure

```
arbitrage_bot/
├── abi/                    # Contract ABIs
├── contracts/              # Smart contracts
├── dashboard/             # Monitoring dashboard
├── configs/               # Configuration files
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

### Testing

Run the test suite:
```bash
python -m pytest
```

## Documentation

- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [Dashboard Guide](docs/DASHBOARD_GUIDE.md)
- [Development Insights](docs/DEVELOPMENT_INSIGHTS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

See [Contributing Guide](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

For security concerns, please email [security contact].

## Support

For support questions, please open an issue in the repository.
