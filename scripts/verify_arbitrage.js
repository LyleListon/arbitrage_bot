// Verify arbitrage system configuration and functionality
const hre = require("hardhat");
const { ethers } = require("hardhat");
const chalk = require("chalk");

async function main() {
    console.log(chalk.blue("\nStarting arbitrage system verification..."));
    
    try {
        // Get deployer account
        const [deployer] = await ethers.getSigners();
        console.log(chalk.gray("Using account:", deployer.address));
        
        // Load deployed contracts
        const contracts = await loadContracts();
        
        // Verify contract deployments
        console.log(chalk.yellow("\nVerifying contract deployments..."));
        await verifyDeployments(contracts);
        
        // Verify component relationships
        console.log(chalk.yellow("\nVerifying component relationships..."));
        await verifyRelationships(contracts);
        
        // Verify DEX configurations
        console.log(chalk.yellow("\nVerifying DEX configurations..."));
        await verifyDEXConfigs(contracts.dexRegistry);
        
        // Verify price feed configurations
        console.log(chalk.yellow("\nVerifying price feed configurations..."));
        await verifyPriceFeedConfigs(contracts.priceFeedRegistry);
        
        // Test basic functionality
        console.log(chalk.yellow("\nTesting basic functionality..."));
        await testBasicFunctionality(contracts);
        
        console.log(chalk.green("\nVerification complete! All checks passed."));
        
    } catch (error) {
        console.error(chalk.red("\nVerification failed:"), error);
        throw error;
    }
}

async function loadContracts() {
    // Load deployment addresses
    const deploymentPath = `./deployments/${hre.network.name}.json`;
    const deployments = require(deploymentPath);
    
    // Load contract factories
    const PriceFeedRegistry = await ethers.getContractFactory("PriceFeedRegistry");
    const DEXRegistry = await ethers.getContractFactory("DEXRegistry");
    const QuoteManager = await ethers.getContractFactory("QuoteManager");
    const PathValidator = await ethers.getContractFactory("PathValidator");
    const PathFinder = await ethers.getContractFactory("PathFinder");
    const MultiPathArbitrage = await ethers.getContractFactory("MultiPathArbitrage");
    const FlashLoanManager = await ethers.getContractFactory("FlashLoanManager");
    const ArbitrageFactory = await ethers.getContractFactory("ArbitrageFactory");
    
    // Load contract instances
    return {
        priceFeedRegistry: PriceFeedRegistry.attach(deployments.priceFeedRegistry),
        dexRegistry: DEXRegistry.attach(deployments.dexRegistry),
        quoteManager: QuoteManager.attach(deployments.quoteManager),
        pathValidator: PathValidator.attach(deployments.pathValidator),
        pathFinder: PathFinder.attach(deployments.pathFinder),
        arbitrageBot: MultiPathArbitrage.attach(deployments.arbitrageBot),
        flashLoanManager: FlashLoanManager.attach(deployments.flashLoanManager),
        factory: ArbitrageFactory.attach(deployments.factory)
    };
}

async function verifyDeployments(contracts) {
    // Verify each contract has code
    for (const [name, contract] of Object.entries(contracts)) {
        const code = await ethers.provider.getCode(contract.address);
        if (code === "0x") {
            throw new Error(`${name} not deployed at ${contract.address}`);
        }
        console.log(chalk.green(`✓ ${name} verified at ${contract.address}`));
    }
}

async function verifyRelationships(contracts) {
    // Verify registry relationships
    const priceFeed = await contracts.arbitrageBot.priceFeedRegistry();
    const dex = await contracts.arbitrageBot.dexRegistry();
    
    if (priceFeed !== contracts.priceFeedRegistry.address) {
        throw new Error("Invalid price feed registry relationship");
    }
    if (dex !== contracts.dexRegistry.address) {
        throw new Error("Invalid DEX registry relationship");
    }
    
    // Verify quote manager relationships
    const quoteManagerDex = await contracts.quoteManager.dexRegistry();
    if (quoteManagerDex !== contracts.dexRegistry.address) {
        throw new Error("Invalid quote manager DEX relationship");
    }
    
    // Verify path validator relationships
    const pathValidatorQuoteManager = await contracts.pathValidator.quoteManager();
    if (pathValidatorQuoteManager !== contracts.quoteManager.address) {
        throw new Error("Invalid path validator quote manager relationship");
    }
    
    // Verify path finder relationships
    const pathFinderValidator = await contracts.pathFinder.pathValidator();
    const pathFinderQuoteManager = await contracts.pathFinder.quoteManager();
    if (pathFinderValidator !== contracts.pathValidator.address) {
        throw new Error("Invalid path finder validator relationship");
    }
    if (pathFinderQuoteManager !== contracts.quoteManager.address) {
        throw new Error("Invalid path finder quote manager relationship");
    }
    
    // Verify flash loan manager relationship
    const flashLoanArbitrageBot = await contracts.flashLoanManager.arbitrageBot();
    if (flashLoanArbitrageBot !== contracts.arbitrageBot.address) {
        throw new Error("Invalid flash loan manager arbitrage bot relationship");
    }
    
    console.log(chalk.green("✓ All component relationships verified"));
}

async function verifyDEXConfigs(dexRegistry) {
    // Get active DEXes
    const activeDEXes = await dexRegistry.getActiveDEXes();
    console.log(chalk.gray(`Found ${activeDEXes.length} active DEXes`));
    
    // Verify each DEX configuration
    for (const dex of activeDEXes) {
        const info = await dexRegistry.getDEXInfo(dex);
        console.log(chalk.gray(`- ${info.protocol}: ${dex}`));
        
        // Verify basic parameters
        if (info.maxSlippage === 0) {
            throw new Error(`Invalid slippage config for ${info.protocol}`);
        }
        if (!info.isActive) {
            throw new Error(`Inactive DEX listed as active: ${info.protocol}`);
        }
        
        console.log(chalk.green(`✓ ${info.protocol} configuration verified`));
    }
}

async function verifyPriceFeedConfigs(priceFeedRegistry) {
    // Get network token configs
    const tokenConfigs = await getNetworkTokenConfigs(hre.network.name);
    
    // Verify each required price feed
    for (const config of tokenConfigs) {
        const hasFeed = await priceFeedRegistry.hasPriceFeed(
            config.baseToken,
            config.quoteToken
        );
        
        if (!hasFeed) {
            throw new Error(`Missing price feed: ${config.symbol}`);
        }
        
        const feed = await priceFeedRegistry.getPriceFeed(
            config.baseToken,
            config.quoteToken
        );
        
        console.log(chalk.green(`✓ ${config.symbol} price feed verified: ${feed}`));
    }
}

async function testBasicFunctionality(contracts) {
    // Test quote generation
    const testAmount = ethers.utils.parseEther("1");
    const tokenConfigs = await getNetworkTokenConfigs(hre.network.name);
    
    if (tokenConfigs.length > 0) {
        const quotes = await contracts.quoteManager.getQuotes(
            tokenConfigs[0].baseToken,
            tokenConfigs[0].quoteToken,
            testAmount,
            ethers.utils.parseUnits("100", "gwei")
        );
        
        console.log(chalk.gray(`Generated ${quotes.length} quotes for test pair`));
    }
    
    // Test path finding
    const paths = await contracts.pathFinder.findPathsWithTokens(
        tokenConfigs[0].baseToken,
        [tokenConfigs[0].quoteToken],
        testAmount,
        ethers.utils.parseUnits("100", "gwei")
    );
    
    console.log(chalk.gray(`Found ${paths.length} potential arbitrage paths`));
    
    // Test flash loan calculation
    const optimalAmount = await contracts.flashLoanManager.calculateOptimalLoanAmount(
        tokenConfigs[0].baseToken,
        testAmount,
        ethers.utils.parseEther("0.1") // 0.1 ETH expected profit
    );
    
    console.log(chalk.gray(`Calculated optimal flash loan amount: ${ethers.utils.formatEther(optimalAmount)} ETH`));
    
    console.log(chalk.green("✓ Basic functionality tests passed"));
}

async function getNetworkTokenConfigs(network) {
    // Example token configs - customize per network
    const configs = {
        mainnet: [
            {
                symbol: "WETH/USDC",
                baseToken: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                quoteToken: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
            }
        ],
        sepolia: [
            {
                symbol: "WETH/USDC",
                baseToken: "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9",
                quoteToken: "0xda9d4f9b69ac6C22e444eD9aF0CfC043b7a7f53f"
            }
        ]
    };
    
    return configs[network] || configs.sepolia;
}

// Execute verification
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = { main };
