const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function main() {
    try {
        console.log("Setting up PancakeSwap pools on Sepolia...");
        
        // Get contracts
        const router = await hre.ethers.getContractAt(
            [
                "function WETH() external pure returns (address)",
                "function factory() external pure returns (address)",
                "function addLiquidityETH(address token, uint amountTokenDesired, uint amountTokenMin, uint amountETHMin, address to, uint deadline) external payable returns (uint amountToken, uint amountETH, uint liquidity)",
                "function swapExactETHForTokens(uint amountOutMin, address[] calldata path, address to, uint deadline) external payable returns (uint[] memory amounts)"
            ],
            config.dex.sepolia.pancakeswapRouter
        );
        
        const factory = await hre.ethers.getContractAt(
            [
                "function getPair(address, address) external view returns (address)",
                "function createPair(address tokenA, address tokenB) external returns (address pair)"
            ],
            config.dex.sepolia.pancakeswapFactory
        );
        
        // Get WETH address
        const WETH = await router.WETH();
        console.log(`WETH address: ${WETH}`);
        
        // Create pairs if they don't exist
        console.log("\nChecking/creating pairs...");
        
        // ETH/USDC pair
        let pair = await factory.getPair(WETH, config.tokens.sepolia.USDC);
        if (pair === "0x0000000000000000000000000000000000000000") {
            console.log("Creating ETH/USDC pair...");
            const tx = await factory.createPair(WETH, config.tokens.sepolia.USDC);
            await tx.wait();
            pair = await factory.getPair(WETH, config.tokens.sepolia.USDC);
        }
        console.log(`ETH/USDC pair: ${pair}`);
        
        // ETH/WBTC pair
        pair = await factory.getPair(WETH, config.tokens.sepolia.WBTC);
        if (pair === "0x0000000000000000000000000000000000000000") {
            console.log("Creating ETH/WBTC pair...");
            const tx = await factory.createPair(WETH, config.tokens.sepolia.WBTC);
            await tx.wait();
            pair = await factory.getPair(WETH, config.tokens.sepolia.WBTC);
        }
        console.log(`ETH/WBTC pair: ${pair}`);
        
        // Add liquidity
        console.log("\nAdding liquidity...");
        
        // Add ETH/USDC liquidity
        console.log("\nAdding ETH/USDC liquidity...");
        const ethAmount = hre.ethers.utils.parseEther("0.1");
        const usdcAmount = hre.ethers.utils.parseUnits("260", 6); // $260 worth of USDC
        
        const deadline = Math.floor(Date.now() / 1000) + 300; // 5 minutes
        
        const tx = await router.addLiquidityETH(
            config.tokens.sepolia.USDC,
            usdcAmount,
            0, // slippage 100%
            0, // slippage 100%
            (await hre.ethers.getSigners())[0].address,
            deadline,
            { value: ethAmount }
        );
        
        await tx.wait();
        console.log("Liquidity added successfully");
        
        // Get pair info
        const pairContract = await hre.ethers.getContractAt(
            [
                "function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)",
                "function token0() external view returns (address)",
                "function token1() external view returns (address)"
            ],
            pair
        );
        
        const [reserve0, reserve1] = await pairContract.getReserves();
        console.log("\nPair Reserves:");
        console.log(`Reserve0: ${reserve0}`);
        console.log(`Reserve1: ${reserve1}`);
        
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
