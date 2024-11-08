/**
 * Base Mainnet Deployment Script for ArbitrageBotV5
 * 
 * This script handles:
 * 1. Contract deployment
 * 2. DEX configuration
 * 3. Token authorization
 * 4. Parameter setting
 * 5. Verification
 * 
 * IMPORTANT: Ensure proper environment variables are set:
 * - MAINNET_RPC_URL
 * - PRIVATE_KEY
 * - ETHERSCAN_API_KEY
 */

const { ethers } = require("hardhat");
const fs = require("fs");

// Configuration constants
const MIN_PROFIT = 200;                         // 2% minimum profit
const MAX_TRADE = ethers.utils.parseEther("1.0"); // 1.0 ETH max trade
const WITHDRAWAL_DELAY = 24 * 60 * 60;          // 24 hours withdrawal delay

// DEX addresses on Base
const DEX_ADDRESSES = {
    baseswap: {
        router: "0xfDf7b675D32D093E3cDD4261F52b448812EF9cD3",
        factory: "0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB",
        type: 0,  // BaseSwap
        priority: 1,
        gasEstimate: 150000
    },
    uniswapV3: {
        router: "0x2626664c2603336E57B271c5C0b26F421741e481",
        factory: "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
        quoter: "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
        type: 1,  // UniswapV3
        priority: 2,
        gasEstimate: 180000
    },
    sushiswap: {
        router: "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        factory: "0xc35DADB65012eC5796536bD9864eD8773aBc74C4",
        type: 2,  // SushiSwap
        priority: 3,
        gasEstimate: 150000
    },
    aerodrome: {
        router: "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
        factory: "0x420DD381b31aEf6683db6B902084cB0FFECe40Da",
        type: 3,  // Aerodrome
        priority: 4,
        gasEstimate: 200000
    }
};

// Token addresses on Base
const TOKEN_ADDRESSES = {
    WETH: "0x4200000000000000000000000000000000000006",
    USDC: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    USDT: "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    DAI: "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"
};

async function main() {
    // Get deployer account
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    console.log("Account balance:", ethers.utils.formatEther(await deployer.getBalance()));

    try {
        // Deploy ArbitrageBotV5
        console.log("\nDeploying ArbitrageBotV5...");
        const ArbitrageBotV5 = await ethers.getContractFactory("ArbitrageBotV5");
        const bot = await ArbitrageBotV5.deploy(
            MIN_PROFIT,
            MAX_TRADE,
            WITHDRAWAL_DELAY
        );
        await bot.deployed();
        console.log("ArbitrageBotV5 deployed to:", bot.address);

        // Setup DEXs
        console.log("\nSetting up DEXs...");
        for (const [name, dex] of Object.entries(DEX_ADDRESSES)) {
            console.log(`Configuring ${name}...`);
            await bot.updateDEX(
                dex.router,
                dex.factory,
                dex.type,
                true, // enabled
                dex.priority,
                dex.gasEstimate
            );
            console.log(`${name} configured successfully`);
        }

        // Setup tokens
        console.log("\nAuthorizing tokens...");
        for (const [symbol, address] of Object.entries(TOKEN_ADDRESSES)) {
            console.log(`Authorizing ${symbol}...`);
            await bot.setAuthorizedToken(address, true);
            console.log(`${symbol} authorized successfully`);
        }

        // Save deployment info
        const deployment = {
            network: "mainnet",
            bot: bot.address,
            timestamp: new Date().toISOString(),
            config: {
                minProfit: MIN_PROFIT,
                maxTrade: MAX_TRADE.toString(),
                withdrawalDelay: WITHDRAWAL_DELAY
            },
            dexes: DEX_ADDRESSES,
            tokens: TOKEN_ADDRESSES
        };

        // Create deployments directory if it doesn't exist
        if (!fs.existsSync("deployments")) {
            fs.mkdirSync("deployments");
        }

        fs.writeFileSync(
            "deployments/mainnet_v5.json",
            JSON.stringify(deployment, null, 2)
        );
        console.log("\nDeployment info saved to deployments/mainnet_v5.json");

        // Verify contract
        console.log("\nVerifying contract on Basescan...");
        await hre.run("verify:verify", {
            address: bot.address,
            constructorArguments: [
                MIN_PROFIT,
                MAX_TRADE,
                WITHDRAWAL_DELAY
            ],
        });
        console.log("Contract verified successfully");

        // Final checks
        console.log("\nPerforming final checks...");
        
        // Check owner
        const owner = await bot.owner();
        console.log("Contract owner:", owner);
        if (owner !== deployer.address) {
            throw new Error("Owner mismatch");
        }

        // Check parameters
        const minProfitCheck = await bot.minProfitBasisPoints();
        const maxTradeCheck = await bot.maxTradeSize();
        const withdrawalDelayCheck = await bot.emergencyWithdrawalDelay();

        console.log("\nContract parameters:");
        console.log("Min Profit:", minProfitCheck.toString(), "basis points");
        console.log("Max Trade:", ethers.utils.formatEther(maxTradeCheck), "ETH");
        console.log("Withdrawal Delay:", withdrawalDelayCheck.toString(), "seconds");

        // Check DEX configuration
        console.log("\nVerifying DEX configuration...");
        for (const [name, dex] of Object.entries(DEX_ADDRESSES)) {
            const dexInfo = await bot.getDEXInfo(dex.router);
            console.log(`${name}:`, dexInfo.enabled ? "Enabled" : "Disabled");
        }

        // Check token authorization
        console.log("\nVerifying token authorization...");
        for (const [symbol, address] of Object.entries(TOKEN_ADDRESSES)) {
            const authorized = await bot.isTokenAuthorized(address);
            console.log(`${symbol}:`, authorized ? "Authorized" : "Unauthorized");
        }

        console.log("\nDeployment complete!");
        console.log("Next steps:");
        console.log("1. Review deployment info in deployments/mainnet_v5.json");
        console.log("2. Test with small amounts first");
        console.log("3. Monitor gas prices and spreads");
        console.log("4. Set up monitoring and alerts");

    } catch (error) {
        console.error("\nDeployment failed:", error);
        process.exit(1);
    }
}

// Execute deployment
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
