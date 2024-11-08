const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("Starting deployment to Sepolia...");

    // Initial parameters (conservative for testing)
    const MIN_PROFIT_BASIS_POINTS = 100;    // 1% minimum profit
    const MAX_TRADE_SIZE = hre.ethers.utils.parseEther("1");  // 1 ETH
    const EMERGENCY_DELAY = 3600;           // 1 hour
    const CIRCUIT_BREAKER = 100;           // Conservative threshold

    try {
        // Get deployer account
        const [deployer] = await hre.ethers.getSigners();
        console.log("Deploying with account:", deployer.address);

        // Deploy ArbitrageBot with fully qualified name
        console.log("\nDeploying ArbitrageBot...");
        const ArbitrageBot = await hre.ethers.getContractFactory("contracts/ArbitrageBot.sol:ArbitrageBot");
        const bot = await ArbitrageBot.deploy(
            MIN_PROFIT_BASIS_POINTS,
            MAX_TRADE_SIZE,
            EMERGENCY_DELAY
        );
        await bot.deployed();
        console.log("ArbitrageBot deployed to:", bot.address);

        // Load configuration
        const configPath = path.join(__dirname, "../dashboard/deploy_config.json");
        const config = JSON.parse(fs.readFileSync(configPath, "utf8"));

        // Authorize DEXes
        console.log("\nAuthorizing DEXes...");
        const dexes = config.dex.sepolia;
        for (const [name, address] of Object.entries(dexes)) {
            console.log(`Authorizing ${name} at ${address}...`);
            await bot.setAuthorizedDEX(address, true);
        }

        // Authorize tokens
        console.log("\nAuthorizing tokens...");
        const tokens = config.tokens.sepolia;
        for (const [symbol, address] of Object.entries(tokens)) {
            console.log(`Authorizing ${symbol} at ${address}...`);
            await bot.setAuthorizedToken(address, true);
        }

        // Verify deployment
        console.log("\nVerifying deployment...");
        console.log("1. Checking parameters...");
        const minProfit = await bot.minProfitBasisPoints();
        const maxTrade = await bot.maxTradeSize();
        const emergencyDelay = await bot.emergencyWithdrawalDelay();
        
        console.log(`- Min Profit: ${minProfit} basis points`);
        console.log(`- Max Trade Size: ${hre.ethers.utils.formatEther(maxTrade)} ETH`);
        console.log(`- Emergency Delay: ${emergencyDelay} seconds`);

        // Test emergency controls
        console.log("\n2. Testing emergency controls...");
        await bot.pause();
        console.log("- Pause successful");
        await bot.unpause();
        console.log("- Unpause successful");

        // Update deployment info
        console.log("\nUpdating deployment configuration...");
        config.contract.address = bot.address;
        config.contract.params = {
            minProfitBasisPoints: MIN_PROFIT_BASIS_POINTS.toString(),
            maxTradeSize: MAX_TRADE_SIZE.toString(),
            emergencyWithdrawalDelay: EMERGENCY_DELAY.toString(),
            circuitBreakerThreshold: CIRCUIT_BREAKER.toString()
        };

        fs.writeFileSync(configPath, JSON.stringify(config, null, 4));
        console.log("Configuration updated successfully");

        // Verify contract on Etherscan
        console.log("\nSubmitting contract for verification...");
        await hre.run("verify:verify", {
            address: bot.address,
            constructorArguments: [
                MIN_PROFIT_BASIS_POINTS,
                MAX_TRADE_SIZE,
                EMERGENCY_DELAY
            ],
        });

        console.log("\nDeployment Summary:");
        console.log("--------------------");
        console.log("Contract Address:", bot.address);
        console.log("Initial Parameters:");
        console.log("- Minimum Profit: 1%");
        console.log("- Maximum Trade Size: 1 ETH");
        console.log("- Emergency Delay: 1 hour");
        console.log("- Circuit Breaker: 100");
        console.log("\nNext Steps:");
        console.log("1. Monitor system for 24 hours without trading");
        console.log("2. Verify price feeds are updating correctly");
        console.log("3. Test emergency controls from dashboard");
        console.log("4. Start with small test trades");

    } catch (error) {
        console.error("Deployment failed:", error);
        process.exit(1);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
