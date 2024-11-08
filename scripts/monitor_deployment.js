const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function checkPriceFeed(feedAddress, name) {
    try {
        const ABI = [
            "function latestRoundData() external view returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound)",
            "function decimals() external view returns (uint8)"
        ];
        const priceFeed = await hre.ethers.getContractAt(ABI, feedAddress);
        const [, answer, , updatedAt] = await priceFeed.latestRoundData();
        const decimals = await priceFeed.decimals();
        const price = answer.toString() / Math.pow(10, decimals);
        const age = Math.floor(Date.now() / 1000) - updatedAt.toNumber();
        return {
            name,
            price: price.toFixed(2),
            age: `${age} seconds`
        };
    } catch (error) {
        return {
            name,
            error: error.message
        };
    }
}

async function main() {
    console.log("Starting deployment monitoring...");
    console.log("Time:", new Date().toISOString());
    console.log("----------------------------------------");

    try {
        // Get contract instance
        const ArbitrageBot = await hre.ethers.getContractFactory("ArbitrageBot");
        const bot = await ArbitrageBot.attach(config.contract.address);

        // Check contract status
        console.log("Contract Status:");
        console.log("----------------------------------------");
        const paused = await bot.paused();
        const minProfit = await bot.minProfitBasisPoints();
        const maxTrade = await bot.maxTradeSize();
        const emergencyDelay = await bot.emergencyWithdrawalDelay();
        const emergencyRequested = await bot.emergencyWithdrawalRequested();

        console.log(`Contract Address: ${config.contract.address}`);
        console.log(`Paused: ${paused}`);
        console.log(`Min Profit: ${minProfit} basis points`);
        console.log(`Max Trade Size: ${hre.ethers.utils.formatEther(maxTrade)} ETH`);
        console.log(`Emergency Delay: ${emergencyDelay} seconds`);
        console.log(`Emergency Requested: ${emergencyRequested}`);

        // Check price feeds
        console.log("\nPrice Feed Status:");
        console.log("----------------------------------------");
        const priceFeeds = config.priceFeeds;
        for (const [name, address] of Object.entries(priceFeeds)) {
            const feedData = await checkPriceFeed(address, name);
            if (feedData.error) {
                console.log(`${feedData.name}: Error - ${feedData.error}`);
            } else {
                console.log(`${feedData.name}:`);
                console.log(`- Price: $${feedData.price}`);
                console.log(`- Last Update: ${feedData.age}`);
            }
        }

        // Check DEX authorizations
        console.log("\nDEX Authorizations:");
        console.log("----------------------------------------");
        const dexes = config.dex.sepolia;
        for (const [name, address] of Object.entries(dexes)) {
            try {
                const isAuthorized = await bot.authorizedDEXs(address);
                console.log(`${name}: ${isAuthorized ? '✓ Authorized' : '✗ Not Authorized'}`);
            } catch (error) {
                console.log(`${name}: Error checking authorization - ${error.message}`);
            }
        }

        // Check token authorizations
        console.log("\nToken Authorizations:");
        console.log("----------------------------------------");
        const tokens = config.tokens.sepolia;
        for (const [symbol, address] of Object.entries(tokens)) {
            try {
                const isAuthorized = await bot.authorizedTokens(address);
                console.log(`${symbol}: ${isAuthorized ? '✓ Authorized' : '✗ Not Authorized'}`);
            } catch (error) {
                console.log(`${symbol}: Error checking authorization - ${error.message}`);
            }
        }

        // Check contract verification
        console.log("\nContract Verification:");
        console.log("----------------------------------------");
        console.log("Etherscan URL:");
        console.log(`https://sepolia.etherscan.io/address/${config.contract.address}`);

    } catch (error) {
        console.error("Monitoring failed:", error);
        process.exit(1);
    }
}

// Run monitoring
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
