// Monitor real arbitrage opportunities on Sepolia
const { ethers } = require("hardhat");
const chalk = require("chalk");
const config = require("../dashboard/config/trading_config.sepolia.yaml");

async function main() {
    console.log(chalk.blue("\nStarting arbitrage opportunity monitoring on Sepolia..."));
    
    try {
        // Connect to contracts
        const contracts = await connectContracts();
        
        // Start monitoring loop
        while (true) {
            await checkOpportunities(contracts);
            await new Promise(resolve => setTimeout(resolve, config.monitoring.update_interval * 1000));
        }
    } catch (error) {
        console.error(chalk.red("\nMonitoring failed:"), error);
        process.exit(1);
    }
}

async function connectContracts() {
    // Connect to deployed contracts
    const MultiPathArbitrage = await ethers.getContractFactory("MultiPathArbitrage");
    const QuoteManager = await ethers.getContractFactory("QuoteManager");
    const PathFinder = await ethers.getContractFactory("PathFinder");
    const PriceFeedRegistry = await ethers.getContractFactory("PriceFeedRegistry");
    const DEXRegistry = await ethers.getContractFactory("DEXRegistry");
    
    return {
        arbitrageBot: MultiPathArbitrage.attach(config.contracts.arbitrage_bot),
        quoteManager: QuoteManager.attach(config.contracts.quote_manager),
        pathFinder: PathFinder.attach(config.contracts.path_finder),
        priceFeedRegistry: PriceFeedRegistry.attach(config.contracts.price_registry),
        dexRegistry: DEXRegistry.attach(config.contracts.dex_registry)
    };
}

async function checkOpportunities(contracts) {
    const timestamp = new Date().toISOString();
    console.log(chalk.gray(`\nChecking opportunities at ${timestamp}`));
    
    // Get network status
    const gasPrice = await ethers.provider.getGasPrice();
    const gasPriceGwei = ethers.utils.formatUnits(gasPrice, "gwei");
    console.log(chalk.gray(`Current gas price: ${gasPriceGwei} gwei`));
    
    // Check each configured pair
    for (const [pairId, pairConfig] of Object.entries(config.pairs)) {
        if (!pairConfig.is_active) continue;
        
        console.log(chalk.yellow(`\nAnalyzing ${pairConfig.display_name}...`));
        
        try {
            // Get Chainlink price as reference
            const chainlinkPrice = await getChainlinkPrice(
                contracts.priceFeedRegistry,
                pairConfig.chainlink_feed
            );
            console.log(chalk.gray(`Chainlink price: $${chainlinkPrice}`));
            
            // Check prices on each DEX
            const prices = await checkDEXPrices(
                contracts,
                pairConfig,
                chainlinkPrice
            );
            
            // Find arbitrage opportunities
            const opportunities = findArbitrageOpportunities(
                prices,
                pairConfig,
                chainlinkPrice,
                gasPrice
            );
            
            // Log opportunities
            if (opportunities.length > 0) {
                console.log(chalk.green(`Found ${opportunities.length} opportunities:`));
                opportunities.forEach(opp => logOpportunity(opp));
            }
            
        } catch (error) {
            console.error(chalk.red(`Error analyzing ${pairConfig.display_name}:`), error);
        }
    }
}

async function getChainlinkPrice(priceFeedRegistry, feedAddress) {
    const aggregator = await ethers.getContractAt("AggregatorV3Interface", feedAddress);
    const [, price, , timestamp] = await aggregator.latestRoundData();
    
    // Check freshness
    const age = Math.floor(Date.now() / 1000) - timestamp;
    if (age > config.monitoring.max_block_delay) {
        throw new Error(`Stale price feed: ${age}s old`);
    }
    
    return parseFloat(ethers.utils.formatUnits(price, 8));
}

async function checkDEXPrices(contracts, pairConfig, referencePrice) {
    const prices = {};
    
    for (const [exchangeId, exchange] of Object.entries(config.exchanges)) {
        if (!exchange.is_active) continue;
        if (!exchange.supported_pairs.includes(pairConfig.display_name)) continue;
        
        try {
            // Get real-time quote from DEX
            const quote = await contracts.quoteManager.getDEXQuote(
                exchange.router,
                pairConfig.base_token,
                pairConfig.quote_token,
                ethers.utils.parseUnits("1", pairConfig.decimals)
            );
            
            // Calculate price deviation
            const price = parseFloat(ethers.utils.formatUnits(quote.output, pairConfig.decimals));
            const deviation = Math.abs((price - referencePrice) / referencePrice * 100);
            
            if (deviation <= config.monitoring.max_price_deviation) {
                prices[exchangeId] = {
                    price,
                    liquidity: quote.liquidity,
                    gasEstimate: quote.gasEstimate
                };
                
                console.log(chalk.gray(`${exchange.name}: $${price.toFixed(2)}`));
            } else {
                console.log(chalk.yellow(`${exchange.name}: Price deviation too high (${deviation.toFixed(1)}%)`));
            }
            
        } catch (error) {
            console.error(chalk.red(`Error getting price from ${exchange.name}:`), error);
        }
    }
    
    return prices;
}

function findArbitrageOpportunities(prices, pairConfig, referencePrice, gasPrice) {
    const opportunities = [];
    const exchanges = Object.entries(prices);
    
    for (let i = 0; i < exchanges.length; i++) {
        for (let j = i + 1; j < exchanges.length; j++) {
            const [buyExchange, buyData] = exchanges[i];
            const [sellExchange, sellData] = exchanges[j];
            
            // Calculate profit potential
            const profitPercentage = ((sellData.price / buyData.price) - 1) * 100;
            
            if (profitPercentage > pairConfig.min_profit_threshold) {
                // Calculate gas cost
                const totalGas = buyData.gasEstimate + sellData.gasEstimate;
                const gasCost = parseFloat(ethers.utils.formatEther(gasPrice.mul(totalGas)));
                
                // Calculate minimum profitable trade size
                const minSize = (gasCost * 2) / profitPercentage;
                
                if (minSize <= pairConfig.max_order_size) {
                    opportunities.push({
                        pair: pairConfig.display_name,
                        buyExchange: config.exchanges[buyExchange].name,
                        sellExchange: config.exchanges[sellExchange].name,
                        profitPercentage,
                        gasCost,
                        minSize,
                        buyPrice: buyData.price,
                        sellPrice: sellData.price,
                        timestamp: Date.now()
                    });
                }
            }
        }
    }
    
    return opportunities;
}

function logOpportunity(opp) {
    console.log(chalk.green(`
    Opportunity found:
    - Pair: ${opp.pair}
    - Buy from ${opp.buyExchange} at $${opp.buyPrice.toFixed(2)}
    - Sell on ${opp.sellExchange} at $${opp.sellPrice.toFixed(2)}
    - Profit: ${opp.profitPercentage.toFixed(2)}%
    - Gas cost: ${opp.gasCost.toFixed(4)} ETH
    - Min size: ${opp.minSize.toFixed(4)} tokens
    `));
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
