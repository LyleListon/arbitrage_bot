const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function main() {
    console.log("Checking token balances...");
    const [signer] = await hre.ethers.getSigners();
    console.log(`Address: ${signer.address}`);
    
    // Check ETH balance
    const ethBalance = await signer.getBalance();
    console.log(`ETH Balance: ${hre.ethers.utils.formatEther(ethBalance)} ETH`);
    
    // Check token balances
    for (const [symbol, address] of Object.entries(config.tokens.sepolia)) {
        try {
            const token = await hre.ethers.getContractAt("IERC20", address);
            const balance = await token.balanceOf(signer.address);
            const decimals = await token.decimals();
            console.log(`${symbol} Balance: ${hre.ethers.utils.formatUnits(balance, decimals)}`);
        } catch (error) {
            console.log(`Error checking ${symbol} balance: ${error.message}`);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
