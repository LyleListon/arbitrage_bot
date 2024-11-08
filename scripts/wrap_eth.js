const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Wrapping ETH to WETH...");

    // WETH address
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";

    // WETH interface
    const wethABI = [
        "function deposit() external payable",
        "function balanceOf(address account) external view returns (uint256)",
        "function withdraw(uint256 wad) external"
    ];

    // Get contracts
    const weth = await ethers.getContractAt(wethABI, WETH);

    // Get signer
    const [signer] = await ethers.getSigners();
    console.log("Using signer:", signer.address);

    try {
        // Check initial balances
        const ethBalance = await ethers.provider.getBalance(signer.address);
        const wethBalance = await weth.balanceOf(signer.address);
        console.log("\nInitial balances:");
        console.log("ETH:", ethers.utils.formatEther(ethBalance));
        console.log("WETH:", ethers.utils.formatEther(wethBalance));

        // Amount to wrap (0.3 ETH)
        const amountToWrap = ethers.utils.parseEther("0.3");
        console.log("\nWrapping:", ethers.utils.formatEther(amountToWrap), "ETH");

        // Wrap ETH
        console.log("Executing deposit...");
        const wrapTx = await weth.deposit({ value: amountToWrap });
        console.log("Waiting for transaction...");
        const receipt = await wrapTx.wait();
        console.log("Transaction hash:", receipt.transactionHash);
        console.log("Wrap successful!");

        // Check final balances
        const finalEthBalance = await ethers.provider.getBalance(signer.address);
        const finalWethBalance = await weth.balanceOf(signer.address);

        console.log("\nFinal balances:");
        console.log("ETH:", ethers.utils.formatEther(finalEthBalance));
        console.log("WETH:", ethers.utils.formatEther(finalWethBalance));

        // Calculate and display changes
        const ethChange = ethBalance.sub(finalEthBalance);
        const wethChange = finalWethBalance.sub(wethBalance);
        console.log("\nBalance changes:");
        console.log("ETH:", ethers.utils.formatEther(ethChange));
        console.log("WETH:", ethers.utils.formatEther(wethChange));

    } catch (error) {
        console.error("\nError wrapping ETH:", error.message);
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
