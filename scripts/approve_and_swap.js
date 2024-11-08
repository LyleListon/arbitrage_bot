const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Approving USDC and attempting minimal swap...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Router addresses
    const swapRouter = "0xE592427A0AEce92De3Edee1F18E0157C05861564";

    // Interfaces
    const erc20ABI = [
        "function approve(address spender, uint256 amount) external returns (bool)",
        "function balanceOf(address account) external view returns (uint256)",
        "function allowance(address owner, address spender) external view returns (uint256)"
    ];

    const routerABI = [
        "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external returns (uint256 amountOut)"
    ];

    // Get contracts
    const router = await ethers.getContractAt(routerABI, swapRouter);
    const weth = await ethers.getContractAt(erc20ABI, WETH);
    const usdc = await ethers.getContractAt(erc20ABI, USDC);

    // Get signer
    const [signer] = await ethers.getSigners();
    console.log("Using signer:", signer.address);

    try {
        // Check initial balances
        const wethBalance = await weth.balanceOf(signer.address);
        const usdcBalance = await usdc.balanceOf(signer.address);
        console.log("\nInitial balances:");
        console.log("WETH:", ethers.utils.formatEther(wethBalance));
        console.log("USDC:", ethers.utils.formatUnits(usdcBalance, 6));

        // Approve USDC
        console.log("\nApproving USDC...");
        const usdcApproveTx = await usdc.approve(swapRouter, ethers.constants.MaxUint256);
        await usdcApproveTx.wait();
        console.log("USDC approved!");

        // Verify approval
        const usdcAllowance = await usdc.allowance(signer.address, swapRouter);
        console.log("New USDC allowance:", ethers.utils.formatUnits(usdcAllowance, 6));

        // Try minimal swap (0.001 WETH)
        const amountIn = ethers.utils.parseEther("0.001");
        console.log("\nSwapping:", ethers.utils.formatEther(amountIn), "WETH");

        // Set very low minimum output for testing
        const minAmountOut = ethers.utils.parseUnits("1", 6); // 1 USDC minimum
        console.log("Minimum USDC output:", ethers.utils.formatUnits(minAmountOut, 6));

        // Prepare swap parameters
        const params = {
            tokenIn: WETH,
            tokenOut: USDC,
            fee: 3000,
            recipient: signer.address,
            deadline: Math.floor(Date.now() / 1000) + 3600,
            amountIn: amountIn,
            amountOutMinimum: minAmountOut,
            sqrtPriceLimitX96: 0
        };

        // Execute swap
        console.log("\nExecuting swap...");
        const swapTx = await router.exactInputSingle(params, { gasLimit: 1000000 });
        console.log("Waiting for transaction...");
        const receipt = await swapTx.wait();
        console.log("Transaction hash:", receipt.transactionHash);
        console.log("Swap successful!");

        // Check final balances
        const finalWethBalance = await weth.balanceOf(signer.address);
        const finalUsdcBalance = await usdc.balanceOf(signer.address);

        console.log("\nFinal balances:");
        console.log("WETH:", ethers.utils.formatEther(finalWethBalance));
        console.log("USDC:", ethers.utils.formatUnits(finalUsdcBalance, 6));

        // Calculate and display changes
        const wethChange = wethBalance.sub(finalWethBalance);
        const usdcChange = finalUsdcBalance.sub(usdcBalance);
        console.log("\nBalance changes:");
        console.log("WETH:", ethers.utils.formatEther(wethChange));
        console.log("USDC:", ethers.utils.formatUnits(usdcChange, 6));

        // Update status file
        console.log("\nUpdating SWAP_STATUS.md with results...");

    } catch (error) {
        console.error("\nError during operation:", error.message);
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
