const hre = require("hardhat");

async function main() {
    console.log("Updating QuoteManager's DEXRegistry...");

    // Get QuoteManager contract
    const quoteManagerAddress = "0x25092401912B59D3F5424003cb68f3196652b848";
    const QuoteManager = await hre.ethers.getContractFactory("QuoteManager");
    const quoteManager = await QuoteManager.attach(quoteManagerAddress);

    // New DEXRegistry address
    const newDexRegistryAddress = "0x8430a08a22e71C1e34BcC52e4d5d4D6ba34f644C";

    try {
        // Get current parameters
        const [signer] = await hre.ethers.getSigners();
        console.log("Using signer:", signer.address);

        // Update DEXRegistry
        console.log("\nUpdating DEXRegistry address to:", newDexRegistryAddress);
        const tx = await quoteManager.setDEXRegistry(newDexRegistryAddress);
        console.log("Waiting for transaction confirmation...");
        await tx.wait();
        console.log("DEXRegistry updated successfully!");

        // Verify update
        console.log("\nVerifying update...");
        const currentDexRegistry = await quoteManager.dexRegistry();
        console.log("Current DEXRegistry:", currentDexRegistry);

        if (currentDexRegistry.toLowerCase() === newDexRegistryAddress.toLowerCase()) {
            console.log("Update verified successfully!");
        } else {
            console.error("Update verification failed!");
            console.log("Expected:", newDexRegistryAddress);
            console.log("Got:", currentDexRegistry);
        }

    } catch (error) {
        console.error("\nError updating QuoteManager:", error.message);

        // Try to get more error details
        if (error.error) {
            console.error("\nError details:", error.error);
        }
        if (error.transaction) {
            console.error("\nTransaction that caused error:", error.transaction);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
