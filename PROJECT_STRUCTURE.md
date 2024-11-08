# Project Structure

## Core Components

### Smart Contracts (/contracts)
- Core arbitrage logic
- DEX integrations
- Price feed implementations
- Cross-chain functionality

### Dashboard (/dashboard)
- Web interface for monitoring
- Analytics and reporting
- Trade execution monitoring
- Price analysis tools

### Configuration
- Network-specific configs in /docs/deployment
- Main config.json for active setup
- Environment templates

## Directory Structure

### /abi
- Contract ABIs for all deployed contracts
- Interface definitions
- Registry ABIs

### /contracts
- Smart contract source code
- Test contracts
- Contract interfaces
- Utility contracts

### /dashboard
- Web interface components
- Monitoring systems
- Analytics tools
- Database schemas
- Frontend assets

### /docs
- Project documentation
- Deployment records
- Setup guides
- Status reports

### /scripts
- Deployment scripts
- Testing utilities
- Maintenance scripts

### /test
- Contract test suites
- Integration tests
- System tests

## Key Files

### Root Directory
- config.json: Active configuration
- config.yaml: System parameters
- hardhat.config.js: Network settings
- package.json: Dependencies
- requirements.txt: Python dependencies

### Dashboard
- app.py: Main dashboard application
- trade_executor.py: Trade execution logic
- price_analysis.py: Price analysis tools
- blockchain_monitor.py: Chain monitoring

## Development Notes

1. Contract Development
   - All contracts use Solidity 0.8.19
   - Hardhat for deployment and testing
   - Extensive test coverage required

2. Dashboard Development
   - Python-based web interface
   - Real-time monitoring
   - Database-backed analytics

3. Configuration Management
   - Network-specific configs in /docs/deployment
   - Environment-based configuration
   - Secure credential management

4. Testing
   - Contract tests in /test
   - Integration tests for dashboard
   - System-wide testing scripts
