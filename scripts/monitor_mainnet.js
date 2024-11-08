// Monitor mainnet operations and system health
const { ethers } = require("hardhat");
const chalk = require("chalk");
const fs = require("fs");
const path = require("path");

// Configuration
const CONFIG = {
    checkInterval: 60000, // 1 minute
    alertThresholds: {
        gasPrice: 150, // gwei
        priceDeviation: 2, // 2%
        minLiquidity: 10000, // $10k
        maxPriceAge: 3600, // 1 hour
        errorRate: 5, // 5%
        profitThreshold: 0.5 // 0.5%
    },
    logFile: path.join(__dirname, '../logs/mainnet_monitor.log')
};

// Monitoring state
let state = {
    lastCheck: 0,
    errorCount: 0,
    successCount: 0,
    totalProfit: ethers.BigNumber.from(0),
    activePaths: new Set(),
    priceCache: new Map(),
    alerts: []
};

async function main() {
    console.log(chalk.blue("\nStarting mainnet monitoring..."));
    
    try {
        // Load contracts
        const contracts = await loadContracts();
        
        // Start monitoring loop
        while (true) {
            await monitorSystem(contracts);
            await new Promise(resolve => setTimeout(resolve, CONFIG.checkInterval));
        }
    } catch (error) {
        console.error(chalk.red("\nMonitoring failed:"), error);
        logError(error);
        process.exit(1);
    }
}

async function loadContracts() {
    // Load deployment addresses
    const deployments = require('../deployments/mainnet.json');
    
    // Load contract factories
    const MultiPathArbitrage = await ethers.getContractFactory("MultiPathArbitrage");
    const QuoteManager = await ethers.getContractFactory("QuoteManager");
    const PathFinder = await ethers.getContractFactory("PathFinder");
    const FlashLoanManager = await ethers.getContractFactory("FlashLoanManager");
    const PriceFeedRegistry = await ethers.getContractFactory("PriceFeedRegistry");
    const DEXRegistry = await ethers.getContractFactory("DEXRegistry");
    
    // Return contract instances
    return {
        arbitrageBot: MultiPathArbitrage.attach(deployments.arbitrageBot),
        quoteManager: QuoteManager.attach(deployments.quoteManager),
        pathFinder: PathFinder.attach(deployments.pathFinder),
        flashLoanManager: FlashLoanManager.attach(deployments.flashLoanManager),
        priceFeedRegistry: PriceFeedRegistry.attach(deployments.priceFeedRegistry),
        dexRegistry: DEXRegistry.attach(deployments.dexRegistry)
    };
}

async function monitorSystem(contracts) {
    const timestamp = Date.now();
    console.log(chalk.gray(`\nSystem check at ${new Date(timestamp).toISOString()}`));
    
    try {
        // Check system health
        await checkSystemHealth(contracts);
        
        // Monitor prices and liquidity
        await monitorMarketConditions(contracts);
        
        // Check for arbitrage opportunities
        await monitorArbitrageOpportunities(contracts);
        
        // Process any alerts
        processAlerts();
        
        // Log status
        logStatus();
        
        state.lastCheck = timestamp;
        state.errorCount = 0;
        
    } catch (error) {
        console.error(chalk.red("Error during monitoring:"), error);
        logError(error);
        state.errorCount++;
        
        if (state.errorCount >= 3) {
            raiseAlert("CRITICAL", "Multiple monitoring failures", error.message);
        }
    }
}

async function checkSystemHealth(contracts) {
    console.log(chalk.yellow("Checking system health..."));
    
    // Check gas prices
    const gasPrice = await ethers.provider.getGasPrice();
    const gasPriceGwei = ethers.utils.formatUnits(gasPrice, "gwei");
    if (parseFloat(gasPriceGwei) > CONFIG.alertThresholds.gasPrice) {
        raiseAlert("WARNING", "High gas price", `Current: ${gasPriceGwei} gwei`);
    }
    
    // Check contract states
    const isPaused = await contracts.arbitrageBot.paused();
    if (isPaused) {
        raiseAlert("WARNING", "System paused", "Arbitrage bot is currently paused");
    }
    
    // Check price feed health
    await checkPriceFeeds(contracts.priceFeedRegistry);
    
    // Check DEX status
    await checkDEXStatus(contracts.dexRegistry);
    
    console.log(chalk.green("✓ System health check complete"));
}

async function checkPriceFeeds(priceFeedRegistry) {
    const feeds = await priceFeedRegistry.getActivePriceFeeds();
    
    for (const feed of feeds) {
        const lastUpdate = await priceFeedRegistry.getLastUpdateTime(feed);
        const age = Math.floor(Date.now() / 1000) - lastUpdate.toNumber();
        
        if (age > CONFIG.alertThresholds.maxPriceAge) {
            raiseAlert("WARNING", "Stale price feed", `Feed ${feed} last updated ${age}s ago`);
        }
    }
}

async function checkDEXStatus(dexRegistry) {
    const dexes = await dexRegistry.getActiveDEXes();
    
    for (const dex of dexes) {
        const info = await dexRegistry.getDEXInfo(dex);
        if (!info.isActive) {
            raiseAlert("WARNING", "Inactive DEX", `DEX ${info.protocol} is inactive`);
        }
    }
}

async function monitorMarketConditions(contracts) {
    console.log(chalk.yellow("Monitoring market conditions..."));
    
    // Get supported trading pairs
    const pairs = await getSupportedPairs(contracts);
    
    for (const pair of pairs) {
        // Check liquidity
        const liquidity = await checkPairLiquidity(contracts, pair);
        if (liquidity < CONFIG.alertThresholds.minLiquidity) {
            raiseAlert("WARNING", "Low liquidity", `${pair.symbol}: $${liquidity}`);
        }
        
        // Check price deviation
        const deviation = await checkPriceDeviation(contracts, pair);
        if (deviation > CONFIG.alertThresholds.priceDeviation) {
            raiseAlert("WARNING", "High price deviation", `${pair.symbol}: ${deviation}%`);
        }
    }
    
    console.log(chalk.green("✓ Market conditions check complete"));
}

async function monitorArbitrageOpportunities(contracts) {
    console.log(chalk.yellow("Checking arbitrage opportunities..."));
    
    // Get supported pairs
    const pairs = await getSupportedPairs(contracts);
    
    for (const pair of pairs) {
        try {
            // Find arbitrage paths
            const paths = await contracts.pathFinder.findPathsWithTokens(
                pair.baseToken,
                [pair.quoteToken],
                ethers.utils.parseEther("1"),
                ethers.utils.parseUnits("100", "gwei")
            );
            
            // Analyze opportunities
            for (const path of paths) {
                if (path.expectedProfit > CONFIG.alertThresholds.profitThreshold) {
                    logOpportunity(pair, path);
                }
            }
        } catch (error) {
            logError(`Error checking opportunities for ${pair.symbol}: ${error.message}`);
        }
    }
    
    console.log(chalk.green("✓ Arbitrage check complete"));
}

function raiseAlert(level, title, message) {
    const alert = {
        level,
        title,
        message,
        timestamp: Date.now()
    };
    
    state.alerts.push(alert);
    
    // Log alert
    const color = level === "CRITICAL" ? chalk.red : chalk.yellow;
    console.log(color(`[${level}] ${title}: ${message}`));
    logAlert(alert);
    
    // TODO: Implement external alerting (e.g., Discord, Telegram)
}

function processAlerts() {
    // Process and clear alerts
    if (state.alerts.length > 0) {
        const criticalAlerts = state.alerts.filter(a => a.level === "CRITICAL");
        if (criticalAlerts.length > 0) {
            // TODO: Implement emergency response for critical alerts
        }
        
        state.alerts = [];
    }
}

function logStatus() {
    const status = {
        timestamp: Date.now(),
        errorCount: state.errorCount,
        successCount: state.successCount,
        totalProfit: state.totalProfit.toString(),
        activePaths: Array.from(state.activePaths),
        alerts: state.alerts
    };
    
    fs.appendFileSync(CONFIG.logFile, JSON.stringify(status) + '\n');
}

function logError(error) {
    fs.appendFileSync(
        CONFIG.logFile,
        `[ERROR] ${new Date().toISOString()}: ${error.message}\n${error.stack}\n`
    );
}

function logAlert(alert) {
    fs.appendFileSync(
        CONFIG.logFile,
        `[ALERT] ${new Date().toISOString()}: ${alert.level} - ${alert.title}: ${alert.message}\n`
    );
}

function logOpportunity(pair, path) {
    fs.appendFileSync(
        CONFIG.logFile,
        `[OPPORTUNITY] ${new Date().toISOString()}: ${pair.symbol} - Profit: ${path.expectedProfit}%\n`
    );
}

// Execute monitoring
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = { main };
