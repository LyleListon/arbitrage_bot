// Script to unpause the arbitrage bot
const hre = require("hardhat");

async function main() {
    console.log("\n=== Unpausing Bot ===\n");

    // Get deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("Using account:", deployer.address);

    // Get contract instance
    const botAddress = process.env.ARBITRAGE_BOT_ADDRESS;
    console.log("Bot address:", botAddress);

    const ArbitrageBot = await hre.ethers.getContractFactory("ArbitrageBot");
    const bot = ArbitrageBot.attach(botAddress);

    // Unpause the bot
    console.log("\nUnpausing bot...");
    const tx = await bot.unpause();
    await tx.wait();

    // Verify the bot is unpaused
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
