const hre = require("hardhat");

// Uniswap V3 addresses on Sepolia
const ADDRESSES = {
    positionManager: "0x1238536071E1c677A632429e3655c799b22cDA52", // NonfungiblePositionManager
    WETH: "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    USDC: "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8",
    WBTC: "0x29f2D40B0605204364af54EC677bD022dA425d03"
};

async function approveToken(token, spender, amount) {
    const tokenContract = await hre.ethers.getContractAt("IERC20", token);
    console.log(`Approving ${amount} of token ${token} for spender ${spender}...`);
    const tx = await tokenContract.approve(spender, amount);
    await tx.wait();
    console.log("Approval successful");
}

async function createPool(positionManager, token0, token1, fee, sqrtPriceX96) {
    try {
        console.log(`\nCreating pool for ${token0}/${token1} with ${fee/10000}% fee...`);
        
        const tx = await positionManager.createAndInitializePoolIfNecessary(
            token0,
            token1,
            fee,
            sqrtPriceX96,
            { gasLimit: 5000000 }
        );
        
        const receipt = await tx.wait();
        console.log(`Pool creation tx: ${receipt.transactionHash}`);
        
        return true;
    } catch (error) {
        console.error(`Error creating pool: ${error.message}`);
        return false;
    }
}

async function main() {
    try {
        console.log("Creating Uniswap V3 pools on Sepolia...");
        
        // Get position manager contract
        const positionManager = await hre.ethers.getContractAt(
            "INonfungiblePositionManager",
            ADDRESSES.positionManager
        );
        
        // Initial price for ETH/USDC: 1 ETH = 2600 USDC
        // sqrt(2600) * 2^96
        const ethUsdcPrice = "3323406039105959588437001438";
        
        // Initial price for ETH/WBTC: 1 ETH = 0.037 WBTC
        // sqrt(0.037) * 2^96
        const ethWbtcPrice = "396164626891866709901370";
        
        // Create WETH/USDC pool
        console.log("\nSetting up WETH/USDC pool...");
        await createPool(
            positionManager,
            ADDRESSES.WETH,
            ADDRESSES.USDC,
            3000, // 0.3% fee
            ethUsdcPrice
        );
        
        // Create WETH/WBTC pool
        console.log("\nSetting up WETH/WBTC pool...");
        await createPool(
            positionManager,
            ADDRESSES.WETH,
            ADDRESSES.WBTC,
            3000, // 0.3% fee
            ethWbtcPrice
        );
        
        console.log("\nPool creation complete!");
        
    } catch (error) {
        console.error("Setup failed:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
