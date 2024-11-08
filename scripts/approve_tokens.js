const hre = require("hardhat");

async function main() {
    console.log("Approving tokens for DEX interactions...");

    // Contract addresses
    const wethAddress = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14"; // Sepolia WETH
    const usdcAddress = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"; // Sepolia USDC
    const uniswapV3Router = "0xE592427A0AEce92De3Edee1F18E0157C05861564";

    try {
        // Get signer
        const [signer] = await hre.ethers.getSigners();
        console.log("Using signer:", signer.address);

        // Get token contracts
        const weth = await hre.ethers.getContractAt("contracts/interfaces/IERC20.sol:IERC20", wethAddress);
        const usdc = await hre.ethers.getContractAt("contracts/interfaces/IERC20.sol:IERC20", usdcAddress);

        // Approve WETH
        console.log("\nApproving WETH...");
        const wethTx = await weth.approve(
            uniswapV3Router,
            hre.ethers.constants.MaxUint256
        );
        console.log("Waiting for WETH approval...");
        await wethTx.wait();
        console.log("WETH approved!");

        // Approve USDC
        console.log("\nApproving USDC...");
        const usdcTx = await usdc.approve(
            uniswapV3Router,
            hre.ethers.constants.MaxUint256
        );
        console.log("Waiting for USDC approval...");
        await usdcTx.wait();
        console.log("USDC approved!");

        // Verify approvals
        console.log("\nVerifying approvals...");
        const wethAllowance = await weth.allowance(signer.address, uniswapV3Router);
        const usdcAllowance = await usdc.allowance(signer.address, uniswapV3Router);

        console.log("WETH allowance:", hre.ethers.utils.formatEther(wethAllowance));
        console.log("USDC allowance:", hre.ethers.utils.formatUnits(usdcAllowance, 6));

    } catch (error) {
        console.error("\nError approving tokens:", error.message);

        // Try to get more error details
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
