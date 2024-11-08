const hre = require("hardhat");

// Uniswap V3 SwapRouter on Sepolia
const SWAP_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564";

// Token addresses
const TOKENS = {
    WETH: "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    USDC: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    WBTC: "0x29f2D40B0605204364af54EC677bD022dA425d03"
};

const ROUTER_ABI = [
    "function exactInputSingle(tuple(address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)",
    "function exactInput(tuple(bytes path, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum)) external payable returns (uint256 amountOut)",
    "function refundETH() external payable"
];

const ERC20_ABI = [
    "function balanceOf(address) external view returns (uint256)",
    "function decimals() external view returns (uint8)",
    "function symbol() external view returns (string)"
];

async function swapETHForToken(token, amountIn, minAmountOut) {
    try {
        const tokenContract = await hre.ethers.getContractAt(ERC20_ABI, token);
        const symbol = await tokenContract.symbol();
        console.log(`\nSwapping ${hre.ethers.utils.formatEther(amountIn)} ETH for ${symbol}...`);
        
        // Get router contract
        const router = await hre.ethers.getContractAt(ROUTER_ABI, SWAP_ROUTER);
        
        // Create swap params
        const [signer] = await hre.ethers.getSigners();
        const params = {
            tokenIn: TOKENS.WETH,
            tokenOut: token,
            fee: 3000, // 0.3%
            recipient: signer.address,
            deadline: Math.floor(Date.now() / 1000) + 300,
            amountIn: amountIn,
            amountOutMinimum: minAmountOut,
            sqrtPriceLimitX96: 0
        };
        
        // Execute swap
        console.log("Executing swap...");
        const tx = await router.exactInputSingle(params, {
            value: amountIn,
            gasLimit: 500000
        });
        
        console.log(`Transaction hash: ${tx.hash}`);
        const receipt = await tx.wait();
        console.log(`Transaction confirmed in block ${receipt.blockNumber}`);
        
        // Check new balance
        const decimals = await tokenContract.decimals();
        const balance = await tokenContract.balanceOf(signer.address);
        console.log(`New ${symbol} balance: ${hre.ethers.utils.formatUnits(balance, decimals)}`);
        
        return true;
    } catch (error) {
        console.error(`Error swapping: ${error.message}`);
        return false;
    }
}

async function main() {
    try {
        console.log("Swapping ETH for tokens on Uniswap V3...");
        
        // Check ETH balance
        const [signer] = await hre.ethers.getSigners();
        const ethBalance = await signer.getBalance();
        console.log(`ETH Balance: ${hre.ethers.utils.formatEther(ethBalance)} ETH`);
        
        // Swap ETH for USDC
        const usdcAmount = hre.ethers.utils.parseEther("0.1"); // Use 0.1 ETH
        await swapETHForToken(TOKENS.USDC, usdcAmount, 0);
        
        // Swap ETH for WBTC
        const wbtcAmount = hre.ethers.utils.parseEther("0.1"); // Use 0.1 ETH
        await swapETHForToken(TOKENS.WBTC, wbtcAmount, 0);
        
        console.log("\nSwaps complete!");
        
    } catch (error) {
        console.error("Failed to swap tokens:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
