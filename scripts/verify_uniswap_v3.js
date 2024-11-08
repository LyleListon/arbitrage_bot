const hre = require("hardhat");

// Uniswap V3 addresses on Sepolia
const ADDRESSES = {
    factory: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    router: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    quoter: "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
    WETH: "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    USDC: "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8",
    WBTC: "0x29f2D40B0605204364af54EC677bD022dA425d03"
};

const FEE_TIERS = [500, 3000, 10000]; // 0.05%, 0.3%, 1%

async function verifyPool(factory, token0, token1, fee) {
    try {
        const pool = await factory.getPool(token0, token1, fee);
        if (pool === "0x0000000000000000000000000000000000000000") {
            return { exists: false };
        }

        const poolContract = await hre.ethers.getContractAt("IUniswapV3Pool", pool);
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
        console.error(`Error verifying pool: ${error.message}`);
        return { exists: false, error: error.message };
    }
}

async function main() {
    try {
        console.log("Verifying Uniswap V3 setup on Sepolia...");
        console.log("\nContract Addresses:");
        console.log("-------------------");
        Object.entries(ADDRESSES).forEach(([name, address]) => {
            console.log(`${name}: ${address}`);
        });

        // Get factory contract
        const factory = await hre.ethers.getContractAt(
            [
                "function getPool(address,address,uint24) external view returns (address)",
                "function owner() external view returns (address)"
            ],
            ADDRESSES.factory
        );

        // Verify factory
        console.log("\nVerifying Factory...");
        try {
            const owner = await factory.owner();
            console.log(`Factory owner: ${owner}`);
        } catch (error) {
            console.log(`Error getting factory owner: ${error.message}`);
        }

        // Check WETH/USDC pools
        console.log("\nChecking WETH/USDC pools:");
        for (const fee of FEE_TIERS) {
            console.log(`\nFee tier: ${fee/10000}%`);
            const poolInfo = await verifyPool(factory, ADDRESSES.WETH, ADDRESSES.USDC, fee);
            if (poolInfo.exists) {
                console.log(`Pool address: ${poolInfo.address}`);
                console.log(`Liquidity: ${poolInfo.liquidity}`);
                console.log(`Current tick: ${poolInfo.tick}`);
            } else {
                console.log("Pool does not exist");
            }
        }

        // Check WETH/WBTC pools
        console.log("\nChecking WETH/WBTC pools:");
        for (const fee of FEE_TIERS) {
            console.log(`\nFee tier: ${fee/10000}%`);
            const poolInfo = await verifyPool(factory, ADDRESSES.WETH, ADDRESSES.WBTC, fee);
            if (poolInfo.exists) {
                console.log(`Pool address: ${poolInfo.address}`);
                console.log(`Liquidity: ${poolInfo.liquidity}`);
                console.log(`Current tick: ${poolInfo.tick}`);
            } else {
                console.log("Pool does not exist");
            }
        }

        // Update config with verified addresses
        console.log("\nUpdating configuration...");
        const config = require("../dashboard/deploy_config.json");
        
        config.dex.sepolia = {
            ...config.dex.sepolia,
            uniswapV3Router: ADDRESSES.router,
            uniswapV3Factory: ADDRESSES.factory,
            uniswapV3Quoter: ADDRESSES.quoter
        };

        config.tokens.sepolia = {
            ...config.tokens.sepolia,
            WETH: ADDRESSES.WETH,
            USDC: ADDRESSES.USDC,
            WBTC: ADDRESSES.WBTC
        };

        const fs = require("fs");
        fs.writeFileSync(
            "dashboard/deploy_config.json",
            JSON.stringify(config, null, 4)
        );

        console.log("Configuration updated with verified Sepolia addresses");

    } catch (error) {
        console.error("Verification failed:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
