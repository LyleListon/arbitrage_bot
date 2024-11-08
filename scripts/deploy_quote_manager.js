const hre = require("hardhat");

async function main() {
    console.log("Deploying new QuoteManager...");

    // Get DEXRegistry address from config
    const dexRegistryAddress = "0xc6BbdD9063A9d247F21BE0C71aAbd95b1C312e8B";  // From config.yaml
    console.log("Using DEXRegistry at:", dexRegistryAddress);

    // Deploy QuoteManager
    const QuoteManager = await hre.ethers.getContractFactory("QuoteManager");
    const quoteManager = await QuoteManager.deploy(dexRegistryAddress);
    await quoteManager.deployed();

    console.log("\nQuoteManager deployed to:", quoteManager.address);

    // Verify deployment
    console.log("\nVerifying deployment...");
    const registry = await quoteManager.dexRegistry();
    console.log("DEXRegistry:", registry);

    if (registry.toLowerCase() === dexRegistryAddress.toLowerCase()) {
        console.log("\nDeployment verified successfully!");
    } else {
        console.error("\nDeployment verification failed!");
        console.log("Expected DEXRegistry:", dexRegistryAddress);
        console.log("Got DEXRegistry:", registry);
    }

    // Set liquidity thresholds
    console.log("\nSetting liquidity thresholds...");
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";  // Sepolia WETH
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";  // Sepolia USDC

    // Only set thresholds for WETH and USDC since those are the tokens we have
    const tokens = [WETH, USDC];
    // Lower the threshold to 0.01 ETH to make testing easier
    const thresholds = tokens.map(() => hre.ethers.utils.parseEther("0.01"));

    const tx = await quoteManager.batchSetLiquidityThresholds(tokens, thresholds);
    await tx.wait();
    console.log("Liquidity thresholds set successfully!");

    console.log("\nDon't forget to:");
    console.log("1. Update config.yaml with the new QuoteManager address:", quoteManager.address);
    console.log("2. Deploy a new PathFinder with the new QuoteManager");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
