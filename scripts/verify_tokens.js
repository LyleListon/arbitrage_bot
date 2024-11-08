const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Verifying token implementations and approvals...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Router addresses
    const swapRouter = "0xE592427A0AEce92De3Edee1F18E0157C05861564";
    const swapRouter02 = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45";

    // Token interface
    const erc20ABI = [
        "function name() external view returns (string)",
        "function symbol() external view returns (string)",
        "function decimals() external view returns (uint8)",
        "function totalSupply() external view returns (uint256)",
        "function balanceOf(address account) external view returns (uint256)",
        "function allowance(address owner, address spender) external view returns (uint256)",
        "function approve(address spender, uint256 amount) external returns (bool)",
        "function transfer(address recipient, uint256 amount) external returns (bool)",
        "function transferFrom(address sender, address recipient, uint256 amount) external returns (bool)"
    ];

    // Get signer
    const [signer] = await ethers.getSigners();
    console.log("Using signer:", signer.address);

    // Get token contracts
    const weth = await ethers.getContractAt(erc20ABI, WETH);
    const usdc = await ethers.getContractAt(erc20ABI, USDC);

    try {
        // Check WETH implementation
        console.log("\nWETH Implementation:");
        console.log("Name:", await weth.name());
        console.log("Symbol:", await weth.symbol());
        console.log("Decimals:", await weth.decimals());
        console.log("Total Supply:", ethers.utils.formatEther(await weth.totalSupply()));
        console.log("Balance:", ethers.utils.formatEther(await weth.balanceOf(signer.address)));

        // Check USDC implementation
        console.log("\nUSDC Implementation:");
        console.log("Name:", await usdc.name());
        console.log("Symbol:", await usdc.symbol());
        console.log("Decimals:", await usdc.decimals());
        console.log("Total Supply:", ethers.utils.formatUnits(await usdc.totalSupply(), 6));
        console.log("Balance:", ethers.utils.formatUnits(await usdc.balanceOf(signer.address), 6));

        // Check WETH approvals
        console.log("\nWETH Approvals:");
        const wethSwapRouterAllowance = await weth.allowance(signer.address, swapRouter);
        const wethSwapRouter02Allowance = await weth.allowance(signer.address, swapRouter02);
        console.log("SwapRouter:", ethers.utils.formatEther(wethSwapRouterAllowance));
        console.log("SwapRouter02:", ethers.utils.formatEther(wethSwapRouter02Allowance));

        // Check USDC approvals
        console.log("\nUSDC Approvals:");
        const usdcSwapRouterAllowance = await usdc.allowance(signer.address, swapRouter);
        const usdcSwapRouter02Allowance = await usdc.allowance(signer.address, swapRouter02);
        console.log("SwapRouter:", ethers.utils.formatUnits(usdcSwapRouterAllowance, 6));
        console.log("SwapRouter02:", ethers.utils.formatUnits(usdcSwapRouter02Allowance, 6));

        // Test WETH transfer
        console.log("\nTesting WETH transfer (0.001 WETH)...");
        const testAmount = ethers.utils.parseEther("0.001");
        const transferTx = await weth.transfer(signer.address, testAmount);
        await transferTx.wait();
        console.log("Transfer successful!");

        // Test USDC transfer
        console.log("\nTesting USDC transfer (0.1 USDC)...");
        const testUsdcAmount = ethers.utils.parseUnits("0.1", 6);
        const usdcTransferTx = await usdc.transfer(signer.address, testUsdcAmount);
        await usdcTransferTx.wait();
        console.log("Transfer successful!");

    } catch (error) {
        console.error("\nError verifying tokens:", error.message);
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
