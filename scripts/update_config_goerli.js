const fs = require('fs');
const yaml = require('js-yaml');
const path = require('path');

// Goerli addresses and configuration
const GOERLI = {
    // Core contracts
    factory: '0x1F98431c8aD98523631AE4a59f267346ea31F984',
    router: '0xE592427A0AEce92De3Edee1F18E0157C05861564',
    quoter: '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',

    // Tokens
    WETH: '0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6',
    USDC: '0x07865c6e87b9f70255377e024ace6630c1eaa37f',

    // Known pools
    'WETH/USDC-0.3%': '0x6337B3caf9C5236c7f3D1694410776119eDaF9FA',

    // Useful contracts
    positionManager: '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',
    swapRouter02: '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45'
};

async function main() {
    console.log("Updating configuration files for Goerli...");

    // Update config.yaml
    try {
        const configPath = path.join(process.cwd(), 'config.yaml');
        console.log("\nUpdating", configPath);

        let config = yaml.load(fs.readFileSync(configPath, 'utf8'));

        // Update network configuration
        config.network = {
            name: 'goerli',
            chainId: 5,
            contracts: {
                factory: GOERLI.factory,
                router: GOERLI.router,
                quoter: GOERLI.quoter,
                positionManager: GOERLI.positionManager,
                swapRouter02: GOERLI.swapRouter02
            },
            tokens: {
                WETH: GOERLI.WETH,
                USDC: GOERLI.USDC
            },
            pools: {
                'WETH/USDC-0.3%': GOERLI['WETH/USDC-0.3%']
            }
        };

        // Update token addresses
        config.tokens = {
            ...(config.tokens || {}),
            WETH: GOERLI.WETH,
            USDC: GOERLI.USDC
        };

        // Save updated config
        fs.writeFileSync(configPath, yaml.dump(config));
        console.log("✓ config.yaml updated");
    } catch (error) {
        console.error("Error updating config.yaml:", error.message);
    }

    // Update dashboard/deploy_config.json
    try {
        const deployConfigPath = path.join(process.cwd(), 'dashboard', 'deploy_config.json');
        console.log("\nUpdating", deployConfigPath);

        const deployConfig = {
            network: "goerli",
            contracts: {
                factory: GOERLI.factory,
                router: GOERLI.router,
                quoter: GOERLI.quoter,
                positionManager: GOERLI.positionManager,
                swapRouter02: GOERLI.swapRouter02
            },
            tokens: {
                WETH: GOERLI.WETH,
                USDC: GOERLI.USDC
            },
            pools: {
                'WETH/USDC-0.3%': GOERLI['WETH/USDC-0.3%']
            }
        };

        fs.writeFileSync(deployConfigPath, JSON.stringify(deployConfig, null, 2));
        console.log("✓ deploy_config.json updated");
    } catch (error) {
        console.error("Error updating deploy_config.json:", error.message);
    }

    // Create .env.goerli template
    try {
        const envPath = path.join(process.cwd(), '.env.goerli');
        console.log("\nCreating", envPath);

        const envContent = `# Goerli Configuration
NETWORK=goerli
CHAIN_ID=5

# Node URL (replace with your Infura/Alchemy URL)
RPC_URL=https://goerli.infura.io/v3/YOUR-PROJECT-ID

# Contract Addresses
FACTORY_ADDRESS=${GOERLI.factory}
ROUTER_ADDRESS=${GOERLI.router}
QUOTER_ADDRESS=${GOERLI.quoter}
POSITION_MANAGER_ADDRESS=${GOERLI.positionManager}
SWAP_ROUTER02_ADDRESS=${GOERLI.swapRouter02}

# Token Addresses
WETH_ADDRESS=${GOERLI.WETH}
USDC_ADDRESS=${GOERLI.USDC}

# Pool Addresses
WETH_USDC_POOL=${GOERLI['WETH/USDC-0.3%']}

# Your wallet private key (DO NOT COMMIT!)
PRIVATE_KEY=your-private-key-here

# Gas settings
GAS_LIMIT=3000000
GAS_PRICE=auto`;

        fs.writeFileSync(envPath, envContent);
        console.log("✓ .env.goerli template created");
    } catch (error) {
        console.error("Error creating .env.goerli:", error.message);
    }

    console.log("\nConfiguration update complete!");
    console.log("\nNext steps:");
    console.log("1. Update .env.goerli with your private key and RPC URL");
    console.log("2. Run 'npx hardhat run scripts/goerli_setup.js --network goerli' to verify setup");
    console.log("3. Test basic operations on Goerli network");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
