// Verify Sepolia configuration and connections
const { ethers } = require("hardhat");
const chalk = require("chalk");
const yaml = require('js-yaml');
const fs = require('fs');
const path = require('path');

async function main() {
    console.log(chalk.blue("\nVerifying Sepolia configuration..."));
    
    try {
        // Load config
        const configPath = path.join(__dirname, '../dashboard/config/trading_config.sepolia.yaml');
        const config = yaml.load(fs.readFileSync(configPath, 'utf8'));
        
        // Check network connection
        await verifyNetwork();
        
        // Check price feeds
        await verifyPriceFeeds(config);
        
        // Check DEX connections
        await verifyDEXes(config);
        
        // Check token balances and approvals
        await verifyTokens(config);
        
        // Check contract deployments
        await verifyContracts(config);
        
        console.log(chalk.green("\n✓ All verifications passed"));
        
    } catch (error) {
        console.error(chalk.red("\nVerification failed:"), error);
        process.exit(1);
    }
}

async function verifyNetwork() {
    console.log(chalk.yellow("\nVerifying network connection..."));
    
    // Check connection
    const network = await ethers.provider.getNetwork();
    if (network.chainId !== 11155111) {
        throw new Error(`Wrong network: expected Sepolia (11155111), got ${network.chainId}`);
    }
    
    // Check block sync
    const block = await ethers.provider.getBlock("latest");
    const blockAge = Math.floor(Date.now() / 1000) - block.timestamp;
    if (blockAge > 60) {
        throw new Error(`Chain not synced: latest block is ${blockAge}s old`);
    }
    
    // Check gas price
    const gasPrice = await ethers.provider.getGasPrice();
    console.log(chalk.gray(`Current gas price: ${ethers.utils.formatUnits(gasPrice, "gwei")} gwei`));
    
    console.log(chalk.green("✓ Network connection verified"));
}

async function verifyPriceFeeds(config) {
    console.log(chalk.yellow("\nVerifying price feeds..."));
    
    for (const [pairId, pairConfig] of Object.entries(config.pairs)) {
        if (!pairConfig.is_active) continue;
        
        console.log(chalk.gray(`\nChecking ${pairConfig.display_name}...`));
        
        // Check feed exists
        const aggregator = await ethers.getContractAt(
            "AggregatorV3Interface",
            pairConfig.chainlink_feed
        );
        
        // Check decimals
        const decimals = await aggregator.decimals();
        console.log(chalk.gray(`Decimals: ${decimals}`));
        
        // Get latest price
        const [, price, , timestamp] = await aggregator.latestRoundData();
        console.log(chalk.gray(`Latest price: $${ethers.utils.formatUnits(price, decimals)}`));
        
        // Check freshness
        const age = Math.floor(Date.now() / 1000) - timestamp;
        if (age > config.monitoring.max_block_delay) {
            throw new Error(`Stale price feed for ${pairConfig.display_name}: ${age}s old`);
        }
        
        console.log(chalk.green(`✓ ${pairConfig.display_name} price feed verified`));
    }
}

async function verifyDEXes(config) {
    console.log(chalk.yellow("\nVerifying DEX connections..."));
    
    for (const [exchangeId, exchange] of Object.entries(config.exchanges)) {
        if (!exchange.is_active) continue;
        
        console.log(chalk.gray(`\nChecking ${exchange.name}...`));
        
        // Check router
        const router = await ethers.getContractAt(
            "contracts/interfaces/IUniswapV3Router.sol:IUniswapV3Router",
            exchange.router
        );
        
        // Check factory
        const factory = await router.factory();
        if (factory !== exchange.factory) {
            throw new Error(`Invalid factory for ${exchange.name}`);
        }
        
        // Check each supported pair
        for (const pairId of exchange.supported_pairs) {
            const pairConfig = config.pairs[pairId];
            if (!pairConfig.is_active) continue;
            
            // Check each fee tier
            for (const feeTier of exchange.fee_tiers) {
                // Get pool address
                const factoryContract = await ethers.getContractAt(
                    "contracts/interfaces/IUniswapV3Factory.sol:IUniswapV3Factory",
                    factory
                );
                const pool = await factoryContract.getPool(
                    pairConfig.base_token,
                    pairConfig.quote_token,
                    feeTier
                );
                
                if (pool !== ethers.constants.AddressZero) {
                    // Check pool liquidity
                    const poolContract = await ethers.getContractAt(
                        "contracts/interfaces/IUniswapV3Pool.sol:IUniswapV3Pool",
                        pool
                    );
                    const liquidity = await poolContract.liquidity();
                    console.log(chalk.gray(`${pairConfig.display_name} (${feeTier/10000}%) liquidity: ${ethers.utils.formatEther(liquidity)}`));
                }
            }
        }
        
        console.log(chalk.green(`✓ ${exchange.name} verified`));
    }
}

async function verifyTokens(config) {
    console.log(chalk.yellow("\nVerifying tokens..."));
    
    const [signer] = await ethers.getSigners();
    
    for (const [pairId, pairConfig] of Object.entries(config.pairs)) {
        if (!pairConfig.is_active) continue;
        
        console.log(chalk.gray(`\nChecking ${pairConfig.display_name}...`));
        
        // Check base token
        const baseToken = await ethers.getContractAt(
            "IERC20",
            pairConfig.base_token
        );
        const baseBalance = await baseToken.balanceOf(signer.address);
        console.log(chalk.gray(`Base token balance: ${ethers.utils.formatUnits(baseBalance, pairConfig.decimals)}`));
        
        // Check quote token
        const quoteToken = await ethers.getContractAt(
            "IERC20",
            pairConfig.quote_token
        );
        const quoteBalance = await quoteToken.balanceOf(signer.address);
        console.log(chalk.gray(`Quote token balance: ${ethers.utils.formatUnits(quoteBalance, pairConfig.decimals)}`));
        
        // Check approvals for each DEX
        for (const [exchangeId, exchange] of Object.entries(config.exchanges)) {
            if (!exchange.is_active || !exchange.supported_pairs.includes(pairId)) continue;
            
            const baseAllowance = await baseToken.allowance(signer.address, exchange.router);
            const quoteAllowance = await quoteToken.allowance(signer.address, exchange.router);
            
            console.log(chalk.gray(`${exchange.name} allowances: ${ethers.utils.formatUnits(baseAllowance, pairConfig.decimals)}, ${ethers.utils.formatUnits(quoteAllowance, pairConfig.decimals)}`));
        }
        
        console.log(chalk.green(`✓ ${pairConfig.display_name} tokens verified`));
    }
}

async function verifyContracts(config) {
    console.log(chalk.yellow("\nVerifying contract deployments..."));
    
    // Check each contract has code
    const contracts = [
        config.contracts.price_registry,
        config.contracts.dex_registry,
        config.contracts.arbitrage_bot,
        config.contracts.quote_manager,
        config.contracts.path_validator,
        config.contracts.path_finder,
        config.contracts.flash_loan_manager,
        config.contracts.factory
    ];
    
    for (const address of contracts) {
        const code = await ethers.provider.getCode(address);
        if (code === "0x") {
            throw new Error(`No code at ${address}`);
        }
    }
    
    console.log(chalk.green("✓ Contract deployments verified"));
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
