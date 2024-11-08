const hre = require("hardhat");

async function main() {
    console.log("Checking PathFinder contract...");

    // Get PathFinder contract
    const pathFinderAddress = "0x80951cC213b54CF41F4f7e5aA04dB14e3c7855a7";  // Latest PathFinder
    const PathFinder = await hre.ethers.getContractFactory("PathFinder");
    const pathFinder = await PathFinder.attach(pathFinderAddress);

    try {
        // Get current parameters
        const maxGasPerPath = await pathFinder.maxGasPerPath();
        const minLiquidityRequired = await pathFinder.minLiquidityRequired();
        const maxPriceImpact = await pathFinder.maxPriceImpact();
        const pathValidator = await pathFinder.pathValidator();
        const quoteManager = await pathFinder.quoteManager();
        const owner = await pathFinder.owner();

        console.log("\nPathFinder Contract Status:");
        console.log("---------------------------");
        console.log("Address:", pathFinderAddress);
        console.log("Owner:", owner);
        console.log("PathValidator:", pathValidator);
        console.log("QuoteManager:", quoteManager);
        console.log("\nParameters:");
        console.log("maxGasPerPath:", maxGasPerPath.toString());
        console.log("minLiquidityRequired:", hre.ethers.utils.formatEther(minLiquidityRequired), "ETH");
        console.log("maxPriceImpact:", maxPriceImpact.toString(), "basis points");

        // Try to find a path to verify contract is working
        const wethAddress = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"; // Sepolia WETH
        const usdcAddress = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"; // Sepolia USDC
        const amount = hre.ethers.utils.parseEther("0.1");
        const gasPrice = await hre.ethers.provider.getGasPrice();

        console.log("\nTesting findBestPath...");
        console.log("Input parameters:");
        console.log("- WETH address:", wethAddress);
        console.log("- USDC address:", usdcAddress);
        console.log("- Amount:", hre.ethers.utils.formatEther(amount), "ETH");
        console.log("- Gas price:", hre.ethers.utils.formatUnits(gasPrice, 'gwei'), "gwei");

        // Try different amounts
        const testAmounts = [
            hre.ethers.utils.parseEther("0.01"),
            hre.ethers.utils.parseEther("0.05"),
            hre.ethers.utils.parseEther("0.1")
        ];

        for (const testAmount of testAmounts) {
            console.log(`\nTesting with amount ${hre.ethers.utils.formatEther(testAmount)} ETH...`);
            try {
                const path = await pathFinder.findBestPath(wethAddress, testAmount, gasPrice);
                console.log("Path found!");
                if (path.tokens && path.tokens.length > 0) {
                    console.log("Tokens:", path.tokens.join(" -> "));
                    console.log("DEXes:", path.dexes.join(" -> "));
                    console.log("Expected profit:", path.expectedProfit ? hre.ethers.utils.formatEther(path.expectedProfit) : "0", "ETH");
                    console.log("Total gas estimate:", path.totalGasEstimate.toString());
                    console.log("Flash loan needed:", path.useFlashLoan);
                } else {
                    console.log("No profitable path found (empty path returned)");
                }
            } catch (error) {
                if (error.message.includes("NoPathFound")) {
                    console.log("No profitable path found");
                } else {
                    console.error("Error finding path:", error.message);
                }
            }
        }

        // Check QuoteManager and DEXRegistry
        console.log("\nChecking QuoteManager and DEXRegistry...");
        console.log("QuoteManager address:", quoteManager);
        const QuoteManager = await hre.ethers.getContractFactory("QuoteManager");
        const quoteManagerContract = await QuoteManager.attach(quoteManager);

        const dexRegistry = await quoteManagerContract.dexRegistry();
        console.log("DEXRegistry:", dexRegistry);

        // Get DEXRegistry contract
        const DEXRegistry = await hre.ethers.getContractFactory("DEXRegistry");
        const dexRegistryContract = await DEXRegistry.attach(dexRegistry);

        // Check active DEXes
        const activeDEXes = await dexRegistryContract.getActiveDEXes();
        console.log("\nActive DEXes:", activeDEXes);

        // Check pair support for each DEX
        const uniswapV3Router = "0xE592427A0AEce92De3Edee1F18E0157C05861564";  // Using router instead of factory
        const isPairSupported = await dexRegistryContract.isPairSupported(
            uniswapV3Router,
            wethAddress,
            usdcAddress
        );
        console.log("\nWETH-USDC pair supported on router:", isPairSupported);

        if (isPairSupported) {
            try {
                const quote = await quoteManagerContract.getDEXQuote(
                    uniswapV3Router,
                    wethAddress,
                    usdcAddress,
                    amount
                );
                console.log("\nQuote received:", {
                    output: hre.ethers.utils.formatEther(quote.output),
                    gasEstimate: quote.gasEstimate.toString(),
                    priceImpact: quote.priceImpact.toString(),
                    liquidity: quote.liquidity.toString()
                });
            } catch (error) {
                console.error("Error getting quote:", error.message);
            }
        } else {
            console.log("Cannot get quote - pair not supported");
        }

    } catch (error) {
        console.error("\nError checking PathFinder contract:", error.message);

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
