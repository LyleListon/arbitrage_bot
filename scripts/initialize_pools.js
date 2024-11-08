const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function addLiquidityETH(router, token, amountToken, amountETH) {
    try {
        const [signer] = await hre.ethers.getSigners();
        
        // Get token contract
        const tokenContract = await hre.ethers.getContractAt("IERC20", token);
        
        // Get router contract with fully qualified name
        const routerContract = await hre.ethers.getContractAt("contracts/interfaces/IUniswapV2Router.sol:IUniswapV2Router", router);
        
        // Approve token
        console.log("Approving token...");
        await tokenContract.approve(router, amountToken);
        
        // Add liquidity
        console.log(`Adding liquidity: ${hre.ethers.utils.formatEther(amountETH)} ETH with ${token}...`);
        const deadline = Math.floor(Date.now() / 1000) + 300; // 5 minutes
        
        const tx = await routerContract.addLiquidityETH(
            token,
            amountToken,
            0, // slippage 100%
            0, // slippage 100%
            signer.address,
            deadline,
            { value: amountETH }
        );
        
        await tx.wait();
        console.log("Liquidity added successfully");
        
        return true;
    } catch (error) {
        console.error(`Error adding liquidity: ${error.message}`);
        return false;
    }
}

async function main() {
    try {
        console.log("Starting pool initialization...");
        
        const [signer] = await hre.ethers.getSigners();
        console.log(`Using address: ${signer.address}`);
        
        // Check ETH balance
        const ethBalance = await signer.getBalance();
        console.log(`ETH Balance: ${hre.ethers.utils.formatEther(ethBalance)} ETH`);
        
        // Calculate amounts based on available ETH
        // Use 90% of available ETH to leave room for gas
        const usableETH = ethBalance.mul(90).div(100);
        console.log(`Usable ETH: ${hre.ethers.utils.formatEther(usableETH)} ETH`);
        
        // Split ETH equally between DEXes and pairs
        const numPools = 6; // 3 DEXes * 2 pairs each
        const ethPerPool = usableETH.div(numPools);
        console.log(`ETH per pool: ${hre.ethers.utils.formatEther(ethPerPool)} ETH`);
        
        if (ethPerPool.lt(hre.ethers.utils.parseEther("0.01"))) {
            console.error("Insufficient ETH per pool. Need at least 0.01 ETH per pool");
            return;
        }
        
        // Calculate token amounts based on current prices
        // Using approximate prices: ETH=$2600, BTC=$71000
        const usdcPerEth = hre.ethers.utils.parseUnits("2600", 6); // USDC has 6 decimals
        const btcPerEth = hre.ethers.utils.parseUnits("0.037", 8); // WBTC has 8 decimals
        
        const usdcAmount = usdcPerEth.mul(ethPerPool).div(hre.ethers.utils.parseEther("1"));
        const wbtcAmount = btcPerEth.mul(ethPerPool).div(hre.ethers.utils.parseEther("1"));
        
        // Initialize pools one by one
        console.log("\nInitializing pools...");
        let successCount = 0;
        
        // Uniswap V2
        console.log("\nUniswap V2:");
        const uniV2Router = config.dex.sepolia.uniswapV2Router;
        if (await addLiquidityETH(uniV2Router, config.tokens.sepolia.USDC, usdcAmount, ethPerPool)) successCount++;
        if (await addLiquidityETH(uniV2Router, config.tokens.sepolia.WBTC, wbtcAmount, ethPerPool)) successCount++;
        
        // Sushiswap
        console.log("\nSushiswap:");
        const sushiRouter = config.dex.sepolia.sushiswapRouter;
        if (await addLiquidityETH(sushiRouter, config.tokens.sepolia.USDC, usdcAmount, ethPerPool)) successCount++;
        if (await addLiquidityETH(sushiRouter, config.tokens.sepolia.WBTC, wbtcAmount, ethPerPool)) successCount++;
        
        // Pancakeswap
        console.log("\nPancakeswap:");
        const pancakeRouter = config.dex.sepolia.pancakeswapRouter;
        if (await addLiquidityETH(pancakeRouter, config.tokens.sepolia.USDC, usdcAmount, ethPerPool)) successCount++;
        if (await addLiquidityETH(pancakeRouter, config.tokens.sepolia.WBTC, wbtcAmount, ethPerPool)) successCount++;
        
        console.log("\nPool initialization complete!");
        console.log(`Successfully initialized ${successCount} out of ${numPools} pools`);
        
    } catch (error) {
        console.error("Pool initialization failed:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
