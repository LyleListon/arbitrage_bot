const hre = require("hardhat");

async function main() {
    console.log("Updating PathFinder's DEXRegistry...");

    // Get PathFinder contract
    const pathFinderAddress = "0x51A469B97c6198112Bef06443D58619b160f16Fe";
    const PathFinder = await hre.ethers.getContractFactory("PathFinder");
    const pathFinder = await PathFinder.attach(pathFinderAddress);

    // New DEXRegistry address
    const newDexRegistryAddress = "0x8430a08a22e71C1e34BcC52e4d5d4D6ba34f644C";

    try {
        // Get current parameters
        const [signer] = await hre.ethers.getSigners();
        console.log("Using signer:", signer.address);

        // Update DEXRegistry
        console.log("\nUpdating DEXRegistry address to:", newDexRegistryAddress);
        const tx = await pathFinder.setDEXRegistry(newDexRegistryAddress);
        console.log("Waiting for transaction confirmation...");
        await tx.wait();
        console.log("DEXRegistry updated successfully!");

        // Verify update
        console.log("\nVerifying update...");
        const currentDexRegistry = await pathFinder.dexRegistry();
        console.log("Current DEXRegistry:", currentDexRegistry);

        if (currentDexRegistry.toLowerCase() === newDexRegistryAddress.toLowerCase()) {
            console.log("Update verified successfully!");
        } else {
            console.error("Update verification failed!");
            console.log("Expected:", newDexRegistryAddress);
            console.log("Got:", currentDexRegistry);
        }

    } catch (error) {
        console.error("\nError updating PathFinder:", error.message);

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
