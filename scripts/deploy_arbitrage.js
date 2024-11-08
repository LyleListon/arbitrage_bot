// Deploy arbitrage system with proper configuration
const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Starting arbitrage system deployment...");
    
    // Get deployer account
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    
    // Initial parameters
    const defaultMinProfitBasisPoints = 50; // 0.5%
    const defaultMaxTradeSize = ethers.utils.parseEther("100"); // 100 tokens
    const emergencyWithdrawalDelay = 3600; // 1 hour
    const maxGasPrice = ethers.utils.parseUnits("100", "gwei"); // 100 gwei
    
    try {
        // Deploy registries first
        console.log("\nDeploying registries...");
        
        const PriceFeedRegistry = await ethers.getContractFactory("contracts/dex/PriceFeedRegistry.sol:PriceFeedRegistry");
        const priceFeedRegistry = await PriceFeedRegistry.deploy();
        await priceFeedRegistry.deployed();
        console.log("PriceFeedRegistry deployed to:", priceFeedRegistry.address);
        
        const DEXRegistry = await ethers.getContractFactory("contracts/dex/DEXRegistry.sol:DEXRegistry");
        const dexRegistry = await DEXRegistry.deploy();
        await dexRegistry.deployed();
        console.log("DEXRegistry deployed to:", dexRegistry.address);
        
        // Deploy core components
        console.log("\nDeploying core components...");
        
        const QuoteManager = await ethers.getContractFactory("contracts/arbitrage/QuoteManager.sol:QuoteManager");
        const quoteManager = await QuoteManager.deploy(dexRegistry.address);
        await quoteManager.deployed();
        console.log("QuoteManager deployed to:", quoteManager.address);
        
        const PathValidator = await ethers.getContractFactory("contracts/arbitrage/PathValidator.sol:PathValidator");
        const pathValidator = await PathValidator.deploy(quoteManager.address);
        await pathValidator.deployed();
        console.log("PathValidator deployed to:", pathValidator.address);
        
        const PathFinder = await ethers.getContractFactory("contracts/arbitrage/PathFinder.sol:PathFinder");
        const pathFinder = await PathFinder.deploy(
            pathValidator.address,
            quoteManager.address
        );
        await pathFinder.deployed();
        console.log("PathFinder deployed to:", pathFinder.address);
        
        const MultiPathArbitrage = await ethers.getContractFactory("contracts/arbitrage/MultiPathArbitrage.sol:MultiPathArbitrage");
        const arbitrageBot = await MultiPathArbitrage.deploy(
            defaultMinProfitBasisPoints,
            defaultMaxTradeSize,
            emergencyWithdrawalDelay
        );
        await arbitrageBot.deployed();
        console.log("MultiPathArbitrage deployed to:", arbitrageBot.address);
        
        // Get Aave Pool Provider address for the current network
        const aaveAddressProvider = await getAaveAddressProvider(hre.network.name);
        
        const FlashLoanManager = await ethers.getContractFactory("contracts/arbitrage/FlashLoanManager.sol:FlashLoanManager");
        const flashLoanManager = await FlashLoanManager.deploy(
            aaveAddressProvider,
            arbitrageBot.address
        );
        await flashLoanManager.deployed();
        console.log("FlashLoanManager deployed to:", flashLoanManager.address);
        
        // Set up relationships
        console.log("\nSetting up component relationships...");
        
        await arbitrageBot.setRegistries(
            priceFeedRegistry.address,
            dexRegistry.address
        );
        console.log("Set registries in arbitrage bot");
        
        await arbitrageBot.setMEVProtection(
            ethers.constants.AddressZero, // No flashbots relayer yet
            false, // Don't use private mempool yet
            maxGasPrice
        );
        console.log("Set MEV protection parameters");
        
        // Configure initial DEXes
        console.log("\nConfiguring initial DEXes...");
        
        const dexConfigs = await getInitialDEXConfigs(hre.network.name);
        for (const config of dexConfigs) {
            await dexRegistry.registerDEX(
                config.router,
                config.protocol,
                config.maxSlippage,
                config.gasOverhead
            );
            console.log(`Registered DEX: ${config.protocol}`);
        }
        
        // Configure initial price feeds
        console.log("\nConfiguring initial price feeds...");
        
        const priceFeedConfigs = await getInitialPriceFeedConfigs(hre.network.name);
        for (const config of priceFeedConfigs) {
            await priceFeedRegistry.registerPriceFeed(
                config.baseToken,
                config.quoteToken,
                config.feed,
                config.stalePriceThreshold
            );
            console.log(`Registered price feed: ${config.baseToken}/${config.quoteToken}`);
        }
        
        // Deploy factory
        console.log("\nDeploying factory...");
        
        const ArbitrageFactory = await ethers.getContractFactory("contracts/arbitrage/ArbitrageFactory.sol:ArbitrageFactory");
        const factory = await ArbitrageFactory.deploy();
        await factory.deployed();
        console.log("ArbitrageFactory deployed to:", factory.address);
        
        // Transfer ownership to factory
        console.log("\nTransferring ownership to factory...");
        
        await arbitrageBot.transferOwnership(factory.address);
        await quoteManager.transferOwnership(factory.address);
        await pathValidator.transferOwnership(factory.address);
        await pathFinder.transferOwnership(factory.address);
        await priceFeedRegistry.transferOwnership(factory.address);
        await dexRegistry.transferOwnership(factory.address);
        
        console.log("\nDeployment complete!");
        
        // Return deployed addresses
        return {
            priceFeedRegistry: priceFeedRegistry.address,
            dexRegistry: dexRegistry.address,
            quoteManager: quoteManager.address,
            pathValidator: pathValidator.address,
            pathFinder: pathFinder.address,
            arbitrageBot: arbitrageBot.address,
            flashLoanManager: flashLoanManager.address,
            factory: factory.address
        };
        
    } catch (error) {
        console.error("Deployment failed:", error);
        throw error;
    }
}

async function getAaveAddressProvider(network) {
    const addressProviders = {
        mainnet: "0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e",
        polygon: "0xd05e3E715d945B59290df0ae8eF85c1BdB684744",
        arbitrum: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
        optimism: "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb",
        sepolia: "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A"
    };
    
    return addressProviders[network] || addressProviders.sepolia;
}

async function getInitialDEXConfigs(network) {
    // Example DEX configs - customize per network
    return [
        {
            router: "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", // Uniswap V2
            protocol: "Uniswap V2",
            maxSlippage: 100, // 1%
            gasOverhead: 150000
        },
        {
            router: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506", // SushiSwap
            protocol: "SushiSwap",
            maxSlippage: 100,
            gasOverhead: 160000
        }
    ];
}

async function getInitialPriceFeedConfigs(network) {
    // Example price feed configs - customize per network
    return [
        {
            baseToken: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", // WETH
            quoteToken: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
            feed: "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419",
            stalePriceThreshold: 3600 // 1 hour
        }
    ];
}

// Execute deployment
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = { main };
