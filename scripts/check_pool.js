const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Checking Uniswap V3 pool details...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Uniswap V3 Factory
    const factoryAddress = "0x0227628f3F023bb0B980b67D528571c95c6DaC1c";

    // Interfaces
    const factoryABI = [
        "function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool)"
    ];

    const poolABI = [
        "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)",
        "function liquidity() external view returns (uint128)",
        "function token0() external view returns (address)",
        "function token1() external view returns (address)",
        "function fee() external view returns (uint24)",
        "function ticks(int24 tick) external view returns (uint128 liquidityGross, int128 liquidityNet, uint256 feeGrowthOutside0X128, uint256 feeGrowthOutside1X128, int56 tickCumulativeOutside, uint160 secondsPerLiquidityOutsideX128, uint32 secondsOutside, bool initialized)"
    ];

    // Get contracts
    const factory = await ethers.getContractAt(factoryABI, factoryAddress);

    // Check pools for different fee tiers
    const feeTiers = [500, 3000, 10000]; // 0.05%, 0.3%, 1%

    for (const fee of feeTiers) {
        console.log(`\nChecking pool with ${fee/10000}% fee...`);

        try {
            const poolAddress = await factory.getPool(WETH, USDC, fee);
            console.log("Pool address:", poolAddress);

            if (poolAddress === ethers.constants.AddressZero) {
                console.log("Pool does not exist");
                continue;
            }

            const pool = await ethers.getContractAt(poolABI, poolAddress);

            // Get pool details
            const token0 = await pool.token0();
            const token1 = await pool.token1();
            const liquidity = await pool.liquidity();
            const slot0 = await pool.slot0();

            console.log("Token0:", token0);
            console.log("Token1:", token1);
            console.log("Liquidity:", liquidity.toString());
            console.log("Current tick:", slot0.tick.toString());
            console.log("Pool unlocked:", slot0.unlocked);

            // Calculate price from sqrtPriceX96
            const Q96 = ethers.BigNumber.from('2').pow(96);
            const priceX96 = slot0.sqrtPriceX96.mul(slot0.sqrtPriceX96).div(Q96);
            const price = priceX96.mul(ethers.utils.parseUnits('1', 6)).div(ethers.utils.parseEther('1'));
            console.log("Price (USDC per ETH):", ethers.utils.formatUnits(price, 6));

            // Check if pool has enough liquidity for a 0.05 ETH swap
            const swapAmount = ethers.utils.parseEther("0.05");
            console.log("\nChecking liquidity for 0.05 ETH swap:");
            console.log("Swap amount:", ethers.utils.formatEther(swapAmount), "ETH");
            console.log("Pool liquidity:", ethers.utils.formatEther(liquidity), "units");

            // Get tick info
            const tickSpacing = fee / 50;
            const tickLower = Math.floor(slot0.tick / tickSpacing) * tickSpacing - tickSpacing;
            const tickUpper = Math.floor(slot0.tick / tickSpacing) * tickSpacing + tickSpacing;

            const lowerTickInfo = await pool.ticks(tickLower);
            const upperTickInfo = await pool.ticks(tickUpper);

            console.log("\nTick info:");
            console.log("Current tick:", slot0.tick);
            console.log("Lower tick:", tickLower);
            console.log("Upper tick:", tickUpper);
            console.log("Lower tick initialized:", lowerTickInfo.initialized);
            console.log("Upper tick initialized:", upperTickInfo.initialized);

        } catch (error) {
            console.log("Error checking pool:", error.message);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
