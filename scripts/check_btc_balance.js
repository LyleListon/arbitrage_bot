const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Checking BTC balance...");

    // Token addresses on Sepolia
    const WBTC = "0x29f2D40B0605204364af54EC677bD022dA425d03";  // Wrapped BTC on Sepolia
    const BTC = "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599";   // Alternative BTC token

    // Token interface
    const erc20ABI = [
        "function balanceOf(address account) external view returns (uint256)",
        "function decimals() external view returns (uint8)",
        "function symbol() external view returns (string)"
    ];

    // Get signer
    const [signer] = await ethers.getSigners();
    console.log("Checking balances for:", signer.address);

    // Check both possible BTC tokens
    const wbtc = await ethers.getContractAt(erc20ABI, WBTC);
    const btc = await ethers.getContractAt(erc20ABI, BTC);

    try {
        const wbtcDecimals = await wbtc.decimals();
        const wbtcSymbol = await wbtc.symbol();
        const wbtcBalance = await wbtc.balanceOf(signer.address);
        console.log(`\n${wbtcSymbol} Balance:`, ethers.utils.formatUnits(wbtcBalance, wbtcDecimals));
    } catch (error) {
        console.log("Could not get WBTC balance:", error.message);
    }

    try {
        const btcDecimals = await btc.decimals();
        const btcSymbol = await btc.symbol();
        const btcBalance = await btc.balanceOf(signer.address);
        console.log(`${btcSymbol} Balance:`, ethers.utils.formatUnits(btcBalance, btcDecimals));
    } catch (error) {
        console.log("Could not get BTC balance:", error.message);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
