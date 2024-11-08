const hre = require("hardhat");

async function main() {
    console.log("Registering DEXes...");

    // Get signer
    const [signer] = await hre.ethers.getSigners();
    console.log("Using signer:", signer.address);

    // Get DEX Registry contract
    const dexRegistryAddress = "0x8430a08a22e71C1e34BcC52e4d5d4D6ba34f644C";
    const DEXRegistry = await hre.ethers.getContractFactory("DEXRegistry");
    const dexRegistry = await DEXRegistry.attach(dexRegistryAddress);

    // Uniswap V3 addresses on Sepolia
    const uniswapV3Factory = "0xc35DADB65012eC5796536bD9864eD8773aBc74C4";
    const uniswapV3Router = "0xE592427A0AEce92De3Edee1F18E0157C05861564";

    // DEX parameters
    const maxSlippage = 100; // 1%
    const estimatedGasOverhead = 150000; // Base gas cost for swap

    try {
        console.log("\nRegistering Uniswap V3...");
        console.log("Factory:", uniswapV3Factory);
        console.log("Router:", uniswapV3Router);
        console.log("Max Slippage:", maxSlippage / 100, "%");
        console.log("Estimated Gas Overhead:", estimatedGasOverhead);

        // Register Uniswap V3 Factory
        console.log("\nRegistering Uniswap V3 Factory...");
        const factoryTx = await dexRegistry.registerDEX(
            uniswapV3Factory,
            "Uniswap V3 Factory",
            maxSlippage,
            estimatedGasOverhead
        );
        console.log("Waiting for factory registration...");
        await factoryTx.wait();
        console.log("Factory registered successfully!");

        // Register Uniswap V3 Router
        console.log("\nRegistering Uniswap V3 Router...");
        const routerTx = await dexRegistry.registerDEX(
            uniswapV3Router,
            "Uniswap V3 Router",
            maxSlippage,
            estimatedGasOverhead
        );
        console.log("Waiting for router registration...");
        await routerTx.wait();
        console.log("Router registered successfully!");

        // Add supported token pairs
        console.log("\nAdding supported token pairs...");
        const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";  // Sepolia WETH
        const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";  // Sepolia USDC
        const LINK = "0x779877A7B0D9E8603169DdbD7836e478b4624789";  // Sepolia LINK
        const DAI = "0x68194a729C2450ad26072b3D33ADaCbcef39D574";   // Sepolia DAI

        const pairs = [
            [WETH, USDC],
            [WETH, LINK],
            [WETH, DAI],
            [USDC, LINK],
            [USDC, DAI],
            [LINK, DAI]
        ];

        // Add pairs to both factory and router
        for (const [baseToken, quoteToken] of pairs) {
            console.log(`Adding pair ${baseToken} - ${quoteToken}...`);

            // Add to factory
            const factoryPairTx = await dexRegistry.addSupportedPair(
                uniswapV3Factory,
                baseToken,
                quoteToken
            );
            await factoryPairTx.wait();
            console.log("Pair added to factory!");

            // Add to router
            const routerPairTx = await dexRegistry.addSupportedPair(
                uniswapV3Router,
                baseToken,
                quoteToken
            );
            await routerPairTx.wait();
            console.log("Pair added to router!");
        }

        // Verify registration
        const activeDEXes = await dexRegistry.getActiveDEXes();
        console.log("\nActive DEXes:", activeDEXes);

        for (const dex of activeDEXes) {
            const info = await dexRegistry.getDEXInfo(dex);
            console.log(`DEX ${dex}:`, {
                protocol: info[0],
                maxSlippage: info[1].toString(),
                isActive: info[2],
                overhead: info[3].toString()
            });
        }

        // Verify pair support
        console.log("\nVerifying pair support...");
        const isFactoryPairSupported = await dexRegistry.isPairSupported(
            uniswapV3Factory,
            WETH,
            USDC
        );
        console.log("WETH-USDC supported on factory:", isFactoryPairSupported);

        const isRouterPairSupported = await dexRegistry.isPairSupported(
            uniswapV3Router,
            WETH,
            USDC
        );
        console.log("WETH-USDC supported on router:", isRouterPairSupported);

    } catch (error) {
        console.error("\nError registering DEXes:", error.message);

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
