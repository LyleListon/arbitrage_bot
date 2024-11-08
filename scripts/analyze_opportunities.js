const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function getTokenPrice(router, tokenIn, tokenOut, amountIn) {
    try {
        const routerContract = await hre.ethers.getContractAt("IUniswapV2Router", router);
        const path = [tokenIn, tokenOut];
        const amounts = await routerContract.getAmountsOut(amountIn, path);
        return amounts[1];
    } catch (error) {
        console.log(`Error getting price from ${router}: ${error.message}`);
        return null;
    }
}

async function main() {
    console.log("Analyzing arbitrage opportunities...");
    console.log("Time:", new Date().toISOString());
    console.log("----------------------------------------");

    try {
        // Get contract instance
        const ArbitrageBot = await hre.ethers.getContractFactory("ArbitrageBot");
        const bot = await ArbitrageBot.attach(config.contract.address);

        // Test amounts
        const testAmounts = [
            hre.ethers.utils.parseEther("0.1"),  // 0.1 ETH
            hre.ethers.utils.parseEther("0.5"),  // 0.5 ETH
            hre.ethers.utils.parseEther("1.0")   // 1.0 ETH
        ];

        // Token pairs to check
        const pairs = [
            { in: config.tokens.sepolia.WETH, out: config.tokens.sepolia.USDC },
            { in: config.tokens.sepolia.WETH, out: config.tokens.sepolia.WBTC },
            { in: config.tokens.sepolia.USDC, out: config.tokens.sepolia.DAI },
            { in: config.tokens.sepolia.WBTC, out: config.tokens.sepolia.USDC }
        ];

        // DEX routers to check
        const dexes = [
            { name: "Uniswap V2", router: config.dex.sepolia.uniswapV2Router },
            { name: "Sushiswap", router: config.dex.sepolia.sushiswapRouter },
            { name: "Pancakeswap", router: config.dex.sepolia.pancakeswapRouter }
        ];

        // Check each amount
        for (const amount of testAmounts) {
            console.log(`\nChecking opportunities for amount: ${hre.ethers.utils.formatEther(amount)} ETH`);
            console.log("----------------------------------------");

            // Check each pair
            for (const pair of pairs) {
                console.log(`\nPair: ${pair.in} -> ${pair.out}`);
                
                // Get prices from different DEXes
                const prices = {};
                for (const dex of dexes) {
                    const price = await getTokenPrice(dex.router, pair.in, pair.out, amount);
                    if (price) {
                        prices[dex.name] = price;
                        console.log(`${dex.name} Price: ${hre.ethers.utils.formatEther(price)}`);
                    }
                }

                // Calculate potential arbitrage
                if (Object.keys(prices).length > 1) {
                    const priceValues = Object.values(prices).map(p => parseFloat(hre.ethers.utils.formatEther(p)));
                    const maxPrice = Math.max(...priceValues);
                    const minPrice = Math.min(...priceValues);
                    const profitBasisPoints = ((maxPrice - minPrice) / minPrice) * 10000;

                    console.log(`Potential profit: ${profitBasisPoints.toFixed(2)} basis points`);
                    
                    // Check if profitable
                    const minProfitBasisPoints = await bot.minProfitBasisPoints();
                    if (profitBasisPoints > minProfitBasisPoints) {
                        console.log("PROFITABLE OPPORTUNITY FOUND!");
                        console.log(`Profit exceeds minimum threshold of ${minProfitBasisPoints} basis points`);
                    } else {
                        console.log(`Profit below minimum threshold of ${minProfitBasisPoints} basis points`);
                    }
                }
            }
        }

        // Check contract balance
        console.log("\nContract Balance Check:");
        console.log("----------------------------------------");
        for (const [symbol, address] of Object.entries(config.tokens.sepolia)) {
            const token = await hre.ethers.getContractAt("IERC20", address);
            const balance = await token.balanceOf(config.contract.address);
            console.log(`${symbol} Balance: ${hre.ethers.utils.formatEther(balance)}`);
        }

        // Simulation summary
        console.log("\nSimulation Summary:");
        console.log("----------------------------------------");
        console.log("1. Contract Status:");
        console.log(`- Paused: ${await bot.paused()}`);
        console.log(`- Min Profit: ${await bot.minProfitBasisPoints()} basis points`);
        console.log(`- Max Trade Size: ${hre.ethers.utils.formatEther(await bot.maxTradeSize())} ETH`);

    } catch (error) {
        console.error("Analysis failed:", error);
        process.exit(1);
    }
}

// Run analysis
main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
