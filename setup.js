const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for console output
 const colors = {
 reset: '\x1b[0m',
bright: '\x1b[1m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m'
};

function log(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    switch(type) {
        case 'success':
            console.log(`${colors.bright}${colors.green}✓ [${timestamp}] ${message}${colors.reset}`);
            break;
        case 'error':
            console.log(`${colors.bright}${colors.red}✗ [${timestamp}] ${message}${colors.reset}`);
            break;
        case 'warning':
            console.log(`${colors.bright}${colors.yellow}⚠ [${timestamp}] ${message}${colors.reset}`);
            break;
        default:
            console.log(`${colors.bright}[${timestamp}] ${message}${colors.reset}`);
    }
}

function runCommand(command, errorMessage) {
    try {
        log(`Running: ${command}`);
        execSync(command, { stdio: 'inherit' });
        log('Command completed successfully', 'success');
        return true;
    } catch (error) {
        log(errorMessage || `Failed to execute: ${command}`, 'error');
        log(error.message, 'error');
        return false;
    }
}

function checkEnvFile() {
    log('Checking .env file...');
    if (!fs.existsSync('.env')) {
        log('.env file not found', 'warning');
        log('Creating .env file template...');
        const envTemplate = 
`MAINNET_RPC_URL=your_sepolia_rpc_url_here
PRIVATE_KEY=your_private_key_here_without_0x
ETHERSCAN_API_KEY=your_etherscan_api_key_here
`;
        fs.writeFileSync('.env', envTemplate);
        log('Created .env template file. Please fill in your values before continuing.', 'warning');
        process.exit(1);
    }
    log('.env file exists', 'success');
}

async function main() {
    try {
        // Check environment
        log('Starting setup process...');
        checkEnvFile();

        // Install dependencies
        log('Installing dependencies...');
        if (!runCommand('npm install --save-dev @nomiclabs/hardhat-ethers@^2.0.0 @nomiclabs/hardhat-waffle ethereum-waffle chai @openzeppelin/contracts --legacy-peer-deps', 
            'Failed to install dependencies')) {
            return;
        }

        // Verify RPC connection
        log('Verifying RPC connection...');
        if (!runCommand('node test/verify_rpc.js',
            'Failed to verify RPC connection. Please check your .env file and network connection')) {
            return;
        }

        // Run tests
        log('Running PriceFeedRegistry tests...');
        if (!runCommand('npx hardhat test test/PriceFeedRegistry.test.js --network hardhat',
            'PriceFeedRegistry tests failed')) {
            return;
        }

        log('Running DEXRegistry tests...');
        if (!runCommand('npx hardhat test test/DEXRegistry.test.js --network hardhat',
            'DEXRegistry tests failed')) {
            return;
        }

        // Final success message
        log('🎉 Setup completed successfully! The project is ready for development.', 'success');
        log(`
Next steps:
1. Implement monitoring system
2. Set up price feed integration
3. Deploy contracts to Sepolia
        `, 'info');

    } catch (error) {
        log('An unexpected error occurred during setup:', 'error');
        log(error.message, 'error');
        process.exit(1);
    }
}

// Run the setup
main().catch(console.error);