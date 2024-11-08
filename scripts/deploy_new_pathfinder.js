const hre = require("hardhat");

async function main() {
    console.log("Deploying new PathFinder...");

    // Contract addresses from config.yaml
    const pathValidatorAddress = "0xA02aFB86Ce774733B543329C2d35Fb663f1755fF";
    const quoteManagerAddress = "0xfeD76Cd4BB823d0E59079C9d2a7f692D2276f408";

    console.log("Using addresses:");
    console.log("PathValidator:", pathValidatorAddress);
    console.log("QuoteManager:", quoteManagerAddress);

    try {
        // Deploy PathFinder
        const PathFinder = await hre.ethers.getContractFactory("PathFinder");
        const pathFinder = await PathFinder.deploy(
            pathValidatorAddress,
            quoteManagerAddress
        );
        await pathFinder.deployed();

        console.log("\nPathFinder deployed to:", pathFinder.address);

        // Verify deployment
        console.log("\nVerifying deployment...");
        const validator = await pathFinder.pathValidator();
        const manager = await pathFinder.quoteManager();

        console.log("Configured addresses:");
        console.log("PathValidator:", validator);
        console.log("QuoteManager:", manager);

        if (validator.toLowerCase() === pathValidatorAddress.toLowerCase() &&
            manager.toLowerCase() === quoteManagerAddress.toLowerCase()) {
            console.log("\nDeployment verified successfully!");
        } else {
            console.error("\nDeployment verification failed!");
            if (validator.toLowerCase() !== pathValidatorAddress.toLowerCase()) {
                console.log("Expected PathValidator:", pathValidatorAddress);
                console.log("Got PathValidator:", validator);
            }
            if (manager.toLowerCase() !== quoteManagerAddress.toLowerCase()) {
                console.log("Expected QuoteManager:", quoteManagerAddress);
                console.log("Got QuoteManager:", manager);
            }
        }

        // Set initial parameters - Optimized for Sepolia testing
        console.log("\nSetting initial parameters...");
        const maxGasPerPath = 300000;  // 300k gas limit per path
        const minLiquidityRequired = hre.ethers.utils.parseEther("0.01"); // 0.01 ETH to match QuoteManager
        const maxPriceImpact = 500; // 5% - reasonable for testing

        const tx = await pathFinder.updateSearchParams(
            maxGasPerPath,
            minLiquidityRequired,
            maxPriceImpact
        );
        await tx.wait();
        console.log("Parameters set successfully!");

        console.log("\nParameters set to:");
        console.log("- Max Gas Per Path:", maxGasPerPath);
        console.log("- Min Liquidity Required:", hre.ethers.utils.formatEther(minLiquidityRequired), "ETH");
        console.log("- Max Price Impact:", maxPriceImpact / 100, "%");

        console.log("\nDon't forget to update config.yaml with the new PathFinder address:", pathFinder.address);

    } catch (error) {
        console.error("\nError deploying PathFinder:", error.message);

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
