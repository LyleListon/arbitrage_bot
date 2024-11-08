const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Swapping WETH to USDC on Uniswap V3...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // SwapRouter on Sepolia
    const routerAddress = "0xE592427A0AEce92De3Edee1F18E0157C05861564";

    // Interfaces
    const routerABI = [
        "function multicall(uint256 deadline, bytes[] data) external payable returns (bytes[])",
        "function exactInput(tuple(bytes path, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum)) external payable returns (uint256 amountOut)",
        "function refundETH() external payable"
    ];

    const erc20ABI = [
        "function approve(address spender, uint256 amount) external returns (bool)",
        "function balanceOf(address account) external view returns (uint256)",
        "function allowance(address owner, address spender) external view returns (uint256)",
        "function transfer(address recipient, uint256 amount) external returns (bool)"
    ];

    // Get contracts
    const router = await ethers.getContractAt(routerABI, routerAddress);
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

        // Amount to swap (0.05 WETH)
        const amountIn = ethers.utils.parseEther("0.05");
        console.log("\nSwapping:", ethers.utils.formatEther(amountIn), "WETH");

        // Set minimum output (assuming 2000 USDC/ETH price with 50% slippage tolerance)
        const minAmountOut = ethers.utils.parseUnits("50", 6); // 50 USDC minimum (0.05 ETH * 2000 * 0.5)
        console.log("Minimum USDC output:", ethers.utils.formatUnits(minAmountOut, 6));

        // Encode the path (WETH -> 0.3% -> USDC)
        const path = ethers.utils.solidityPack(
            ['address', 'uint24', 'address'],
            [WETH, 3000, USDC]
        );

        // Encode approve call
        const approveInterface = new ethers.utils.Interface([
            "function approve(address spender, uint256 amount) external returns (bool)"
        ]);
        const approveData = approveInterface.encodeFunctionData("approve", [
            routerAddress,
            amountIn
        ]);

        // Encode exactInput call
        const swapInterface = new ethers.utils.Interface([
            "function exactInput(tuple(bytes path, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum)) external payable returns (uint256 amountOut)"
        ]);
        const swapData = swapInterface.encodeFunctionData("exactInput", [{
            path: path,
            recipient: signer.address,
            deadline: Math.floor(Date.now() / 1000) + 3600,
            amountIn: amountIn,
            amountOutMinimum: minAmountOut
        }]);

        // Execute multicall
        console.log("\nExecuting multicall...");
        const deadline = Math.floor(Date.now() / 1000) + 3600;
        const multicallTx = await router.multicall(deadline, [approveData, swapData], {
            gasLimit: 1000000
        });
        console.log("Waiting for transaction...");
        const receipt = await multicallTx.wait();
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
        console.error("\nError swapping tokens:", error.message);
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
