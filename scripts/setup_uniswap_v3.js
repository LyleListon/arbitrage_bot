const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function main() {
    try {
        console.log("Setting up Uniswap V3 on Sepolia...");
        
        // Get router contract
        const router = await hre.ethers.getContractAt(
            "contracts/interfaces/ISwapRouter.sol:ISwapRouter",
            config.dex.sepolia.uniswapV3Router
        );
        
        // Define test amounts
        const testAmount = hre.ethers.utils.parseEther("0.1"); // 0.1 ETH
        const deadline = Math.floor(Date.now() / 1000) + 300; // 5 minutes
        
        // Test ETH -> USDC swap
        console.log("\nTesting ETH -> USDC swap...");
        const usdcSwapParams = {
            tokenIn: config.tokens.sepolia.WETH,
            tokenOut: config.tokens.sepolia.USDC,
            fee: 3000, // 0.3%
            recipient: (await hre.ethers.getSigners())[0].address,
            deadline: deadline,
            amountIn: testAmount,
            amountOutMinimum: 0,
            sqrtPriceLimitX96: 0
        };
        
        try {
            const tx = await router.exactInputSingle(usdcSwapParams);
            await tx.wait();
            console.log("USDC swap successful");
        } catch (error) {
            console.log(`USDC swap failed: ${error.message}`);
        }
        
        // Test ETH -> WBTC swap
        console.log("\nTesting ETH -> WBTC swap...");
        const wbtcSwapParams = {
            tokenIn: config.tokens.sepolia.WETH,
            tokenOut: config.tokens.sepolia.WBTC,
            fee: 3000, // 0.3%
            recipient: (await hre.ethers.getSigners())[0].address,
            deadline: deadline,
            amountIn: testAmount,
            amountOutMinimum: 0,
            sqrtPriceLimitX96: 0
        };
        
        try {
            const tx = await router.exactInputSingle(wbtcSwapParams);
            await tx.wait();
            console.log("WBTC swap successful");
        } catch (error) {
            console.log(`WBTC swap failed: ${error.message}`);
        }
        
        // Check token balances
        console.log("\nChecking balances...");
        const [signer] = await hre.ethers.getSigners();
        
        const usdc = await hre.ethers.getContractAt("IERC20", config.tokens.sepolia.USDC);
        const wbtc = await hre.ethers.getContractAt("IERC20", config.tokens.sepolia.WBTC);
        
        const usdcBalance = await usdc.balanceOf(signer.address);
        const wbtcBalance = await wbtc.balanceOf(signer.address);
        
        console.log(`USDC Balance: ${hre.ethers.utils.formatUnits(usdcBalance, 6)}`);
        console.log(`WBTC Balance: ${hre.ethers.utils.formatUnits(wbtcBalance, 8)}`);
        
    } catch (error) {
        console.error("Setup failed:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
