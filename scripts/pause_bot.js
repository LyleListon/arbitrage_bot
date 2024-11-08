// Script to pause the arbitrage bot
const hre = require("hardhat");

async function main() {
    console.log("\n=== Pausing Bot ===\n");

    // Get deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("Using account:", deployer.address);

    // Get contract instance
    const botAddress = process.env.ARBITRAGE_BOT_ADDRESS;
    console.log("Bot address:", botAddress);

    const ArbitrageBot = await hre.ethers.getContractFactory("ArbitrageBot");
    const bot = ArbitrageBot.attach(botAddress);

    // Pause the bot
    console.log("\nPausing bot...");
    const tx = await bot.pause();
    await tx.wait();

    // Verify the bot is paused
    const isPaused = await bot.paused();
    console.log("Bot paused:", isPaused);

    console.log("\nTransaction hash:", tx.hash);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
