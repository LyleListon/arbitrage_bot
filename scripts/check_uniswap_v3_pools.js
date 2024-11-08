const hre = require("hardhat");

// Uniswap V3 addresses on Sepolia
const ADDRESSES = {
    factory: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    WETH: "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    USDC: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
    WBTC: "0x29f2D40B0605204364af54EC677bD022dA425d03"
};

const FACTORY_ABI = [
    "function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool)"
];

const POOL_ABI = [
    "function token0() external view returns (address)",
    "function token1() external view returns (address)",
    "function fee() external view returns (uint24)",
    "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)",
    "function liquidity() external view returns (uint128)"
];

const FEE_AMOUNTS = {
    LOWEST: 100,
    LOW: 500,
    MEDIUM: 3000,
    HIGH: 10000
};

async function checkPool(factory, token0, token1, fee) {
    try {
        const pool = await factory.getPool(token0, token1, fee);
        
        if (pool === "0x0000000000000000000000000000000000000000") {
            return { exists: false };
        }

        const poolContract = await hre.ethers.getContractAt(POOL_ABI, pool);
        const [sqrtPriceX96, tick, , , , , ] = await poolContract.slot0();
        const liquidity = await poolContract.liquidity();

        return {
            exists: true,
            address: pool,
            sqrtPriceX96: sqrtPriceX96.toString(),
            tick: tick.toString(),
            liquidity: liquidity.toString()
        };
    } catch (error) {
        console.error(`Error checking pool: ${error.message}`);
        return { exists: false, error: error.message };
    }
}

async function main() {
    try {
        console.log("Checking Uniswap V3 pools on Sepolia...");
        
        // Get factory contract
        const factory = await hre.ethers.getContractAt(FACTORY_ABI, ADDRESSES.factory);
        
        // Check all fee tiers for WETH/USDC
        console.log("\nChecking WETH/USDC pools:");
        for (const [feeName, fee] of Object.entries(FEE_AMOUNTS)) {
            console.log(`\nFee tier: ${feeName} (${fee/10000}%)`);
            const poolInfo = await checkPool(factory, ADDRESSES.WETH, ADDRESSES.USDC, fee);
            
            if (poolInfo.exists) {
                console.log(`Pool exists at: ${poolInfo.address}`);
                console.log(`Liquidity: ${poolInfo.liquidity}`);
                console.log(`Current tick: ${poolInfo.tick}`);
                if (poolInfo.liquidity === "0") {
                    console.log("WARNING: Pool has no liquidity!");
                }
            } else {
                console.log("Pool does not exist");
            }
        }
        
        // Check all fee tiers for WETH/WBTC
        console.log("\nChecking WETH/WBTC pools:");
        for (const [feeName, fee] of Object.entries(FEE_AMOUNTS)) {
            console.log(`\nFee tier: ${feeName} (${fee/10000}%)`);
            const poolInfo = await checkPool(factory, ADDRESSES.WETH, ADDRESSES.WBTC, fee);
            
            if (poolInfo.exists) {
                console.log(`Pool exists at: ${poolInfo.address}`);
                console.log(`Liquidity: ${poolInfo.liquidity}`);
                console.log(`Current tick: ${poolInfo.tick}`);
                if (poolInfo.liquidity === "0") {
                    console.log("WARNING: Pool has no liquidity!");
                }
            } else {
                console.log("Pool does not exist");
            }
        }
        
    } catch (error) {
        console.error("Check failed:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
