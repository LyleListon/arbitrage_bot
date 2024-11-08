const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function getAmountOut(router, amountIn, path) {
    try {
        const routerContract = await hre.ethers.getContractAt("contracts/interfaces/IUniswapV2Router.sol:IUniswapV2Router", router);
        const amounts = await routerContract.getAmountsOut(amountIn, path);
        return amounts[amounts.length - 1];
    } catch (error) {
        console.error(`Error getting amount out: ${error.message}`);
        return null;
    }
}

async function main() {
    try {
        console.log("Checking arbitrage opportunities...");
        console.log("Time:", new Date().toISOString());
        
        const WETH = config.tokens.sepolia.WETH;
        const USDC = config.tokens.sepolia.USDC;
        const WBTC = config.tokens.sepolia.WBTC;
        
        // Test with different amounts
        const testAmounts = [
            { value: "0.1", wei: hre.ethers.utils.parseEther("0.1") },
            { value: "0.5", wei: hre.ethers.utils.parseEther("0.5") },
            { value: "1.0", wei: hre.ethers.utils.parseEther("1.0") }
        ];
        
        const dexes = [
            { name: "Uniswap V2", router: config.dex.sepolia.uniswapV2Router },
            { name: "Sushiswap", router: config.dex.sepolia.sushiswapRouter }
        ];
        
        // Check ETH -> USDC -> ETH
        console.log("\nChecking ETH -> USDC -> ETH path");
        console.log("----------------------------------------");
        
        for (const amount of testAmounts) {
            console.log(`\nTesting with ${amount.value} ETH:`);
            
            for (const dex of dexes) {
                // ETH -> USDC
                const path1 = [WETH, USDC];
                const usdcOut = await getAmountOut(dex.router, amount.wei, path1);
                
                if (usdcOut) {
                    console.log(`${dex.name}: ${amount.value} ETH -> ${hre.ethers.utils.formatUnits(usdcOut, 6)} USDC`);
                    
                    // USDC -> ETH
                    const path2 = [USDC, WETH];
                    const ethBack = await getAmountOut(dex.router, usdcOut, path2);
                    
                    if (ethBack) {
                        const profitLoss = ethBack.sub(amount.wei);
                        const profitLossEth = hre.ethers.utils.formatEther(profitLoss);
                        console.log(`${dex.name}: ${hre.ethers.utils.formatUnits(usdcOut, 6)} USDC -> ${hre.ethers.utils.formatEther(ethBack)} ETH (${profitLossEth} ETH)`);
                    }
                }
            }
        }
        
        // Check ETH -> WBTC -> ETH
        console.log("\nChecking ETH -> WBTC -> ETH path");
        console.log("----------------------------------------");
        
        for (const amount of testAmounts) {
            console.log(`\nTesting with ${amount.value} ETH:`);
            
            for (const dex of dexes) {
                // ETH -> WBTC
                const path1 = [WETH, WBTC];
                const wbtcOut = await getAmountOut(dex.router, amount.wei, path1);
                
                if (wbtcOut) {
                    console.log(`${dex.name}: ${amount.value} ETH -> ${hre.ethers.utils.formatUnits(wbtcOut, 8)} WBTC`);
                    
                    // WBTC -> ETH
                    const path2 = [WBTC, WETH];
                    const ethBack = await getAmountOut(dex.router, wbtcOut, path2);
                    
                    if (ethBack) {
                        const profitLoss = ethBack.sub(amount.wei);
                        const profitLossEth = hre.ethers.utils.formatEther(profitLoss);
                        console.log(`${dex.name}: ${hre.ethers.utils.formatUnits(wbtcOut, 8)} WBTC -> ${hre.ethers.utils.formatEther(ethBack)} ETH (${profitLossEth} ETH)`);
                    }
                }
            }
        }
        
        // Check cross-DEX opportunities
        console.log("\nChecking Cross-DEX Arbitrage Opportunities");
        console.log("----------------------------------------");
        
        for (const amount of testAmounts) {
            console.log(`\nTesting with ${amount.value} ETH:`);
            
            // ETH -> USDC on Uniswap, USDC -> ETH on Sushiswap
            const uniUsdcOut = await getAmountOut(config.dex.sepolia.uniswapV2Router, amount.wei, [WETH, USDC]);
            if (uniUsdcOut) {
                const sushiEthBack = await getAmountOut(config.dex.sepolia.sushiswapRouter, uniUsdcOut, [USDC, WETH]);
                if (sushiEthBack) {
                    const profitLoss = sushiEthBack.sub(amount.wei);
                    const profitLossEth = hre.ethers.utils.formatEther(profitLoss);
                    console.log(`Uni->Sushi (USDC): ${amount.value} ETH -> ${hre.ethers.utils.formatUnits(uniUsdcOut, 6)} USDC -> ${hre.ethers.utils.formatEther(sushiEthBack)} ETH (${profitLossEth} ETH)`);
                }
            }
            
            // ETH -> WBTC on Uniswap, WBTC -> ETH on Sushiswap
            const uniWbtcOut = await getAmountOut(config.dex.sepolia.uniswapV2Router, amount.wei, [WETH, WBTC]);
            if (uniWbtcOut) {
                const sushiEthBack = await getAmountOut(config.dex.sepolia.sushiswapRouter, uniWbtcOut, [WBTC, WETH]);
                if (sushiEthBack) {
                    const profitLoss = sushiEthBack.sub(amount.wei);
                    const profitLossEth = hre.ethers.utils.formatEther(profitLoss);
                    console.log(`Uni->Sushi (WBTC): ${amount.value} ETH -> ${hre.ethers.utils.formatUnits(uniWbtcOut, 8)} WBTC -> ${hre.ethers.utils.formatEther(sushiEthBack)} ETH (${profitLossEth} ETH)`);
                }
            }
        }
        
    } catch (error) {
        console.error("Error checking arbitrage:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
