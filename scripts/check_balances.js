const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Checking token balances...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Token interfaces
    const erc20ABI = [
        "function balanceOf(address account) external view returns (uint256)",
        "function decimals() external view returns (uint8)",
        "function symbol() external view returns (string)"
    ];

    // Get signer
    const [signer] = await ethers.getSigners();
    console.log("Checking balances for:", signer.address);

    // Get ETH balance
    const ethBalance = await ethers.provider.getBalance(signer.address);
    console.log("\nETH Balance:", ethers.utils.formatEther(ethBalance), "ETH");

    // Get WETH balance
    const weth = await ethers.getContractAt(erc20ABI, WETH);
    const wethBalance = await weth.balanceOf(signer.address);
    console.log("WETH Balance:", ethers.utils.formatEther(wethBalance), "WETH");

    // Get USDC balance
    const usdc = await ethers.getContractAt(erc20ABI, USDC);
    const usdcBalance = await usdc.balanceOf(signer.address);
    console.log("USDC Balance:", ethers.utils.formatUnits(usdcBalance, 6), "USDC");

    // Check if we have enough for adding liquidity
    const neededEth = ethers.utils.parseEther("0.1");
    const neededUsdc = ethers.utils.parseUnits("200", 6);

    console.log("\nRequired amounts for adding liquidity:");
    console.log("ETH needed:", ethers.utils.formatEther(neededEth), "ETH");
    console.log("USDC needed:", ethers.utils.formatUnits(neededUsdc, 6), "USDC");

    if (ethBalance.lt(neededEth)) {
        console.log("\nWARNING: Not enough ETH!");
        console.log("Need", ethers.utils.formatEther(neededEth.sub(ethBalance)), "more ETH");
    }

    if (usdcBalance.lt(neededUsdc)) {
        console.log("\nWARNING: Not enough USDC!");
        console.log("Need", ethers.utils.formatUnits(neededUsdc.sub(usdcBalance), 6), "more USDC");
    }

    if (ethBalance.gte(neededEth) && usdcBalance.gte(neededUsdc)) {
        console.log("\nSUCCESS: Have enough tokens to add liquidity!");
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
