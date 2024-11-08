const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function main() {
    console.log("Starting deployment verification...");
    
    const contractAddress = config.contract.address;
    console.log(`Verifying contract at: ${contractAddress}`);

    try {
        // Get contract instance
        const ArbitrageBot = await hre.ethers.getContractFactory("contracts/ArbitrageBot.sol:ArbitrageBot");
        const bot = await ArbitrageBot.attach(contractAddress);
        
        // Test emergency controls
        console.log("\nTesting emergency controls...");
        
        // 1. Check initial state
        console.log("1. Checking initial state...");
        const initiallyPaused = await bot.paused();
        console.log(`- Initially paused: ${initiallyPaused}`);

        // 2. Test pause
        if (!initiallyPaused) {
            console.log("2. Testing pause...");
            const pauseTx = await bot.pause();
            await pauseTx.wait();
            console.log("- Pause successful");
        }

        // 3. Verify paused state
        const pausedState = await bot.paused();
        console.log(`- Contract paused: ${pausedState}`);

        // 4. Test unpause
        console.log("3. Testing unpause...");
        const unpauseTx = await bot.unpause();
        await unpauseTx.wait();
        console.log("- Unpause successful");

        // 5. Verify final state
        const finalState = await bot.paused();
        console.log(`- Final paused state: ${finalState}`);

        // Verify parameters
        console.log("\nVerifying parameters...");
        const minProfit = await bot.minProfitBasisPoints();
        const maxTrade = await bot.maxTradeSize();
        const emergencyDelay = await bot.emergencyWithdrawalDelay();

        console.log(`- Min Profit: ${minProfit} basis points`);
        console.log(`- Max Trade Size: ${hre.ethers.utils.formatEther(maxTrade)} ETH`);
        console.log(`- Emergency Delay: ${emergencyDelay} seconds`);

        // Verify contract on Etherscan
        console.log("\nVerifying contract on Etherscan...");
        await hre.run("verify:verify", {
            address: contractAddress,
            constructorArguments: [
                config.contract.params.minProfitBasisPoints,
                config.contract.params.maxTradeSize,
                config.contract.params.emergencyWithdrawalDelay
            ],
        });

        console.log("\nVerification completed successfully!");

    } catch (error) {
        console.error("Verification failed:", error);
        process.exit(1);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
