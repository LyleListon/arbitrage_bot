const hre = require("hardhat");

async function main() {
    console.log("Updating PathFinder parameters...");

    // Get PathFinder contract
    const pathFinderAddress = "0x51A469B97c6198112Bef06443D58619b160f16Fe";
    const PathFinder = await hre.ethers.getContractFactory("PathFinder");
    const pathFinder = await PathFinder.attach(pathFinderAddress);

    // Update parameters for Sepolia testnet:
    // - Reduce maxGasPerPath to 300,000 (more reasonable for Sepolia)
    // - Reduce minLiquidityRequired to 0.1 tokens (much lower for testing)
    // - Increase maxPriceImpact to 5% (more lenient for testing)
    const tx = await pathFinder.updateSearchParams(
        300000,              // maxGasPerPath
        hre.ethers.utils.parseEther("0.1"), // minLiquidityRequired
        500                  // maxPriceImpact (5%)
    );

    console.log("Waiting for transaction confirmation...");
    await tx.wait();
    console.log("PathFinder parameters updated successfully!");

    // Verify new parameters
    console.log("\nNew parameters:");
    console.log("maxGasPerPath:", (await pathFinder.maxGasPerPath()).toString());
    console.log("minLiquidityRequired:", hre.ethers.utils.formatEther(await pathFinder.minLiquidityRequired()));
    console.log("maxPriceImpact:", (await pathFinder.maxPriceImpact()).toString());
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
