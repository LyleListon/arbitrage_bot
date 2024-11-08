const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Attempting direct pool swap...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Pool address
    const poolAddress = "0x6Ce0896eAE6D4BD668fDe41BB784548fb8F59b50";

    // Interfaces
    const poolABI = [
        "function swap(address recipient, bool zeroForOne, int256 amountSpecified, uint160 sqrtPriceLimitX96, bytes calldata data) external returns (int256 amount0, int256 amount1)",
        "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)",
        "function token0() external view returns (address)",
        "function token1() external view returns (address)"
    ];

    const erc20ABI = [
        "function approve(address spender, uint256 amount) external returns (bool)",
        "function balanceOf(address account) external view returns (uint256)",
        "function allowance(address owner, address spender) external view returns (uint256)",
        "function transfer(address recipient, uint256 amount) external returns (bool)"
    ];

    // Get contracts
    const pool = await ethers.getContractAt(poolABI, poolAddress);
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

        // Get pool state
        const slot0 = await pool.slot0();
        console.log("\nPool state:");
        console.log("Current tick:", slot0.tick.toString());
        console.log("Pool unlocked:", slot0.unlocked);

        // Get token order
        const token0 = await pool.token0();
        const token1 = await pool.token1();
        console.log("\nToken order:");
        console.log("Token0:", token0);
        console.log("Token1:", token1);

        // Determine swap direction
        const zeroForOne = WETH === token0;
        console.log("\nSwap direction (zeroForOne):", zeroForOne);

        // Amount to swap (0.001 WETH)
        const amountIn = ethers.utils.parseEther("0.001");
        console.log("\nSwapping:", ethers.utils.formatEther(amountIn), "WETH");

        // Approve pool
        console.log("\nApproving pool...");
        const approveTx = await weth.approve(poolAddress, amountIn);
        await approveTx.wait();
        console.log("Pool approved!");

        // Calculate price limit (allow 50% slippage)
        const currentSqrtPrice = slot0.sqrtPriceX96;
        const slippageFactor = ethers.BigNumber.from(2); // 50% slippage
        const sqrtPriceLimit = zeroForOne
            ? currentSqrtPrice.div(slippageFactor)
            : currentSqrtPrice.mul(slippageFactor);

        // Execute swap
        console.log("\nExecuting swap...");
        const swapTx = await pool.swap(
            signer.address,
            zeroForOne,
            amountIn,
            sqrtPriceLimit,
            "0x",
            { gasLimit: 1000000 }
        );
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

    } catch (error) {
        console.error("\nError during swap:", error.message);
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
