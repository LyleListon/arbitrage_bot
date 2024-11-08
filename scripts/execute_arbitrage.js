// Execute real arbitrage trades on Sepolia
const { ethers } = require("hardhat");
const chalk = require("chalk");
const config = require("../dashboard/config/trading_config.sepolia.yaml");

// Safety parameters
const SAFETY = {
    maxSlippage: 100, // 1%
    minProfitUSD: 5, // $5 minimum profit
    maxGasPrice: 50, // 50 gwei
    minLiquidity: ethers.utils.parseEther("1"), // 1 ETH equivalent
    priceValidityDuration: 60, // 1 minute
    maxRetries: 3
};

async function main() {
    console.log(chalk.blue("\nStarting arbitrage execution on Sepolia..."));
    
    try {
        // Connect to contracts
        const contracts = await connectContracts();
        
        // Start execution loop
        while (true) {
            await executeArbitrage(contracts);
            await new Promise(resolve => setTimeout(resolve, config.monitoring.update_interval * 1000));
        }
    } catch (error) {
        console.error(chalk.red("\nExecution failed:"), error);
        process.exit(1);
    }
}

async function connectContracts() {
    // Connect to deployed contracts
    const MultiPathArbitrage = await ethers.getContractFactory("MultiPathArbitrage");
    const QuoteManager = await ethers.getContractFactory("QuoteManager");
    const PathFinder = await ethers.getContractFactory("PathFinder");
    const FlashLoanManager = await ethers.getContractFactory("FlashLoanManager");
    
    return {
        arbitrageBot: MultiPathArbitrage.attach(config.contracts.arbitrage_bot),
        quoteManager: QuoteManager.attach(config.contracts.quote_manager),
        pathFinder: PathFinder.attach(config.contracts.path_finder),
        flashLoanManager: FlashLoanManager.attach(config.contracts.flash_loan_manager)
    };
}

async function executeArbitrage(contracts) {
    const timestamp = new Date().toISOString();
    console.log(chalk.gray(`\nChecking execution at ${timestamp}`));
    
    // Check network conditions
    const networkOK = await checkNetworkConditions();
    if (!networkOK) return;
    
    // Find opportunities
    const opportunities = await findOpportunities(contracts);
    if (opportunities.length === 0) {
        console.log(chalk.gray("No profitable opportunities found"));
        return;
    }
    
    // Execute best opportunity
    const bestOpp = selectBestOpportunity(opportunities);
    await executeTrade(contracts, bestOpp);
}

async function checkNetworkConditions() {
    // Check gas price
    const gasPrice = await ethers.provider.getGasPrice();
    const gasPriceGwei = parseFloat(ethers.utils.formatUnits(gasPrice, "gwei"));
    if (gasPriceGwei > SAFETY.maxGasPrice) {
        console.log(chalk.yellow(`Gas price too high: ${gasPriceGwei} gwei`));
        return false;
    }
    
    // Check network congestion
    const block = await ethers.provider.getBlock("latest");
    if (block.gasUsed.mul(100).div(block.gasLimit).gt(80)) {
        console.log(chalk.yellow("Network congestion too high"));
        return false;
    }
    
    return true;
}

async function findOpportunities(contracts) {
    const opportunities = [];
    
    // Check each configured pair
    for (const [pairId, pairConfig] of Object.entries(config.pairs)) {
        if (!pairConfig.is_active) continue;
        
        try {
            // Find arbitrage paths
            const paths = await contracts.pathFinder.findPathsWithTokens(
                pairConfig.base_token,
                [pairConfig.quote_token],
                ethers.utils.parseUnits("1", pairConfig.decimals),
                ethers.utils.parseUnits(SAFETY.maxGasPrice.toString(), "gwei")
            );
            
            // Validate each path
            for (const path of paths) {
                const validation = await validatePath(contracts, path, pairConfig);
                if (validation.isValid) {
                    opportunities.push({
                        path,
                        config: pairConfig,
                        validation
                    });
                }
            }
            
        } catch (error) {
            console.error(chalk.red(`Error finding opportunities for ${pairConfig.display_name}:`), error);
        }
    }
    
    return opportunities;
}

async function validatePath(contracts, path, pairConfig) {
    // Validate with PathValidator
    const validation = await contracts.pathValidator.validatePath(
        path.tokens,
        path.dexes,
        ethers.utils.parseUnits("1", pairConfig.decimals),
        ethers.utils.parseUnits(SAFETY.maxGasPrice.toString(), "gwei")
    );
    
    if (!validation.isValid) return validation;
    
    // Additional safety checks
    for (let i = 0; i < path.dexes.length; i++) {
        // Check liquidity
        const quote = await contracts.quoteManager.getDEXQuote(
            path.dexes[i],
            path.tokens[i],
            path.tokens[i + 1],
            ethers.utils.parseUnits("1", pairConfig.decimals)
        );
        
        if (quote.liquidity.lt(SAFETY.minLiquidity)) {
            validation.isValid = false;
            validation.reason = "Insufficient liquidity";
            break;
        }
        
        // Check price impact
        if (quote.priceImpact.gt(SAFETY.maxSlippage)) {
            validation.isValid = false;
            validation.reason = "Excessive price impact";
            break;
        }
    }
    
    return validation;
}

function selectBestOpportunity(opportunities) {
    // Sort by profit and pick best
    return opportunities.sort((a, b) => {
        return b.validation.maxProfit.sub(a.validation.maxProfit);
    })[0];
}

async function executeTrade(contracts, opportunity) {
    console.log(chalk.yellow("\nExecuting trade:"));
    console.log(chalk.gray(`- Pair: ${opportunity.config.display_name}`));
    console.log(chalk.gray(`- Expected profit: ${ethers.utils.formatEther(opportunity.validation.maxProfit)} ETH`));
    
    try {
        // Calculate optimal amount
        const amount = await calculateOptimalAmount(contracts, opportunity);
        
        // Check if flash loan would be profitable
        const useFlashLoan = await checkFlashLoanProfitability(contracts, opportunity, amount);
        
        if (useFlashLoan) {
            // Execute with flash loan
            await executeFlashLoanTrade(contracts, opportunity, amount);
        } else {
            // Execute direct trade
            await executeDirectTrade(contracts, opportunity, amount);
        }
        
    } catch (error) {
        console.error(chalk.red("Trade execution failed:"), error);
    }
}

async function calculateOptimalAmount(contracts, opportunity) {
    // Start with minimum size
    let amount = ethers.utils.parseUnits(
        opportunity.config.min_order_size.toString(),
        opportunity.config.decimals
    );
    
    // Calculate gas costs
    const gasPrice = await ethers.provider.getGasPrice();
    const gasCost = gasPrice.mul(opportunity.validation.totalGas);
    
    // Increase size until gas cost is reasonable percentage of profit
    while (gasCost.mul(20).lt(opportunity.validation.maxProfit.mul(amount))) {
        amount = amount.mul(2);
        
        // Check if we've hit maximum size
        if (amount.gt(ethers.utils.parseUnits(
            opportunity.config.max_order_size.toString(),
            opportunity.config.decimals
        ))) {
            amount = ethers.utils.parseUnits(
                opportunity.config.max_order_size.toString(),
                opportunity.config.decimals
            );
            break;
        }
    }
    
    return amount;
}

async function checkFlashLoanProfitability(contracts, opportunity, amount) {
    // Calculate flash loan costs
    const flashLoanAmount = await contracts.flashLoanManager.calculateOptimalLoanAmount(
        opportunity.path.tokens[0],
        amount,
        opportunity.validation.maxProfit
    );
    
    return flashLoanAmount.gt(amount);
}

async function executeFlashLoanTrade(contracts, opportunity, amount) {
    console.log(chalk.yellow("Executing flash loan trade..."));
    
    const params = {
        tokens: opportunity.path.tokens,
        dexes: opportunity.path.dexes,
        amount: amount,
        minProfit: opportunity.validation.minProfit
    };
    
    const tx = await contracts.flashLoanManager.executeWithFlashLoan(
        opportunity.path.tokens[0],
        amount,
        params
    );
    
    console.log(chalk.green("Flash loan trade executed:"), tx.hash);
    await tx.wait();
}

async function executeDirectTrade(contracts, opportunity, amount) {
    console.log(chalk.yellow("Executing direct trade..."));
    
    const tx = await contracts.arbitrageBot.executeMultiPathArbitrage(
        {
            steps: opportunity.path.steps,
            totalGasEstimate: opportunity.validation.totalGas,
            expectedProfit: opportunity.validation.maxProfit,
            useFlashLoan: false
        },
        amount
    );
    
    console.log(chalk.green("Direct trade executed:"), tx.hash);
    await tx.wait();
}

// Execute arbitrage
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = { main };
