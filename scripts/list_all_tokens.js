const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Listing all token balances...");

    const WALLET = "0xb9039E54Ad00ae6559fF91d0db2c1192D0eaA801";

    // Known token addresses on Sepolia
    const tokens = [
        {
            symbol: "WBTC",
            address: "0x29f2D40B0605204364af54EC677bD022dA425d03",
            decimals: 8
        },
        {
            symbol: "WETH",
            address: "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
            decimals: 18
        },
        {
            symbol: "USDC",
            address: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
            decimals: 6
        },
        {
            symbol: "USDC (100k)",
            address: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
            decimals: 6
        },
        {
            symbol: "RareTron.io",
            address: "0x2CdA416424051c0A68e11cE8752a68F7A52f3F03", // This is a guess, need to verify
            decimals: 18
        }
    ];

    // Token interface
    const erc20ABI = [
        "function balanceOf(address account) external view returns (uint256)",
        "function decimals() external view returns (uint8)",
        "function symbol() external view returns (string)"
    ];

    console.log("\nChecking balances for:", WALLET);

    // Get ETH balance
    const ethBalance = await ethers.provider.getBalance(WALLET);
    console.log("\nETH Balance:", ethers.utils.formatEther(ethBalance), "ETH");

    // Check each token
    for (const token of tokens) {
        try {
            const contract = await ethers.getContractAt(erc20ABI, token.address);
            const balance = await contract.balanceOf(WALLET);
            const symbol = await contract.symbol();
            console.log(`${symbol} Balance:`, ethers.utils.formatUnits(balance, token.decimals));
        } catch (error) {
            console.log(`Error getting ${token.symbol} balance:`, error.message);
        }
    }

    // Try to find any other token transfers to this address
    console.log("\nNote: Some tokens might be using different addresses on Sepolia.");
    console.log("Let me know if you need to check any specific token addresses.");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
