const hre = require("hardhat");

// Sepolia faucet contracts
const FAUCETS = {
    USDC: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238", // USDC faucet is the same as token
    WBTC: "0x29f2D40B0605204364af54EC677bD022dA425d03"  // WBTC faucet is the same as token
};

async function mintTestTokens(token, name) {
    try {
        console.log(`\nMinting ${name}...`);
        
        // Get token contract with mint function
        const tokenContract = await hre.ethers.getContractAt(
            [
                "function mint(address to, uint256 amount) external",
                "function balanceOf(address) external view returns (uint256)",
                "function decimals() external view returns (uint8)"
            ],
            token
        );
        
        const [signer] = await hre.ethers.getSigners();
        
        // Get decimals
        const decimals = await tokenContract.decimals();
        
        // Amount to mint
        const mintAmount = name === 'USDC' 
            ? hre.ethers.utils.parseUnits("1000", decimals)  // 1000 USDC
            : hre.ethers.utils.parseUnits("0.1", decimals);  // 0.1 WBTC
        
        // Mint tokens
        console.log(`Minting ${name}...`);
        const tx = await tokenContract.mint(signer.address, mintAmount);
        await tx.wait();
        
        // Check new balance
        const balance = await tokenContract.balanceOf(signer.address);
        console.log(`New ${name} balance: ${hre.ethers.utils.formatUnits(balance, decimals)}`);
        
        return true;
    } catch (error) {
        console.error(`Error minting ${name}: ${error.message}`);
        return false;
    }
}

async function main() {
    try {
        console.log("Getting test tokens on Sepolia...");
        
        // Get USDC
        await mintTestTokens(FAUCETS.USDC, "USDC");
        
        // Get WBTC
        await mintTestTokens(FAUCETS.WBTC, "WBTC");
        
        console.log("\nToken acquisition complete!");
        
    } catch (error) {
        console.error("Failed to get test tokens:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
