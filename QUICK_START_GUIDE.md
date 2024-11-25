# Quick Start Guide: Arbitrage Bot

## Prerequisites
- Python 3.9+
- Node.js 14+
- Git
- Docker (optional but recommended)

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/[your-repo]/arbitrage-bot.git
cd arbitrage-bot
```

### 2. Set Up Python Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Node Dependencies
```bash
npm install
```

### 4. Configure Blockchain Endpoints
1. Copy `configs/local.template.json` to `configs/local.json`
2. Edit `local.json` with your blockchain RPC endpoints
   - Add Ethereum, BSC, Polygon endpoints
   - Configure API keys if required

### 5. Set Environment Variables
```bash
export ARBITRAGE_BOT_CONFIG=configs/local.json
export WEB3_PROVIDER_URI=https://mainnet.infura.io/v3/YOUR-PROJECT-ID
```

### 6. Run Initial Tests
```bash
python -m pytest tests/
```

### 7. Start Dashboard
```bash
python run_dashboard.py
```

## Development Modes

### Local Development
```bash
# Run with development configuration
python run.py --config configs/local.json

# Run dashboard in development mode
python dashboard/app.py --debug
```

### Simulation Mode
```bash
# Run arbitrage simulation
python scripts/backtesting.py --start-date 2023-01-01 --end-date 2023-12-31
```

### Machine Learning Model Training
```bash
# Train price prediction model
python ml_train.py --model xgboost --features price_volume

# Evaluate model performance
python ml_evaluate.py --model models/xgb_model.joblib
```

## Deployment Options

### Docker Deployment
```bash
# Build Docker image
docker build -t arbitrage-bot .

# Run Docker container
docker run -e CONFIG_PATH=/app/configs/production.json arbitrage-bot
```

### Kubernetes Deployment
```bash
# Apply Kubernetes configurations
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Monitoring and Logging

### View Logs
```bash
# Tail application logs
tail -f logs/arbitrage_bot.log

# Monitor dashboard logs
tail -f dashboard/logs/dashboard.log
```

### Performance Metrics
- Access Grafana dashboard at `http://localhost:3000`
- Prometheus metrics endpoint: `http://localhost:9090/metrics`

## Troubleshooting

### Common Issues
- Ensure all environment variables are set
- Check blockchain endpoint connectivity
- Verify API key permissions
- Update dependencies regularly

### Debugging
```bash
# Run with verbose logging
python run.py --log-level DEBUG

# Generate diagnostic report
python scripts/diagnostics.py
```

## Security Recommendations
- Never commit sensitive information (API keys, private keys)
- Use environment-specific configurations
- Regularly update dependencies
- Enable two-factor authentication for all services

## Contributing
- Read CONTRIBUTING.md for detailed guidelines
- Create feature branches for new developments
- Write comprehensive tests
- Follow code style guidelines

## Support
- Check GitHub Issues for known problems
- Join our Discord community for real-time support
- Email support: arbitrage-bot-support@example.com

## Version Information
- Current Version: 1.0.0
- Last Updated: [Current Date]
- Compatibility: Python 3.9+, Web3.py 5.x
