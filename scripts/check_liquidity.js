const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Checking Uniswap V3 WETH-USDC pool liquidity on Sepolia...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Pool interface with swap calculation functions
    const poolABI = [
        "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)",
        "function liquidity() external view returns (uint128)",
        "function token0() external view returns (address)",
        "function token1() external view returns (address)",
        "function fee() external view returns (uint24)",
        "function observe(uint32[] calldata secondsAgos) external view returns (int56[] memory tickCumulatives, uint160[] memory secondsPerLiquidityCumulativeX128s)"
    ];

    // Get pool contract
    const poolAddress = "0x6Ce0896eAE6D4BD668fDe41BB784548fb8F59b50";
    const pool = await ethers.getContractAt(poolABI, poolAddress);

    console.log("\nPool Information:");
    console.log("Address:", poolAddress);

    // Check pool configuration
    const token0 = await pool.token0();
    const token1 = await pool.token1();
    const fee = await pool.fee();
    console.log("\nPool configuration:");
    console.log("Token0 (USDC):", token0);
    console.log("Token1 (WETH):", token1);
    console.log("Fee:", fee.toString(), "basis points");

    // Check pool state
    const liquidity = await pool.liquidity();
    console.log("\nPool state:");
    console.log("Liquidity:", liquidity.toString());

    const slot0 = await pool.slot0();
    console.log("Current tick:", slot0.tick.toString());
    console.log("Current sqrt price:", slot0.sqrtPriceX96.toString());
    console.log("Pool unlocked:", slot0.unlocked);

    // Calculate price from sqrtPriceX96
    const Q96 = ethers.BigNumber.from('2').pow(96);
    const priceX96 = slot0.sqrtPriceX96.mul(slot0.sqrtPriceX96).div(Q96);
    const price = priceX96.mul(ethers.utils.parseUnits('1', 6)).div(ethers.utils.parseEther('1')); // Adjust for decimals
    console.log("\nCalculated price:", ethers.utils.formatUnits(price, 6), "USDC per ETH");

    // Test amounts
    const testAmounts = [
        ethers.utils.parseEther("0.001"),  // 0.001 ETH
        ethers.utils.parseEther("0.01"),   // 0.01 ETH
        ethers.utils.parseEther("0.1")     // 0.1 ETH
    ];

    console.log("\nCalculating expected output amounts:");
    for (const amountIn of testAmounts) {
        // Simple price impact calculation
        const amountOut = amountIn.mul(price).div(ethers.utils.parseEther('1'));
        console.log(`\nFor ${ethers.utils.formatEther(amountIn)} ETH:`);
        console.log("Expected output:", ethers.utils.formatUnits(amountOut, 6), "USDC");

        // Calculate price impact
        const priceImpact = amountIn.mul(10000).div(liquidity);
        console.log("Estimated price impact:", priceImpact.toString(), "basis points");
    }

    // Check recent price movement
    try {
        console.log("\nChecking price movement...");
        const secondsAgos = [0, 60, 300]; // now, 1 min ago, 5 mins ago
        const [tickCumulatives, ] = await pool.observe(secondsAgos);

        console.log("Price movement in last minute:");
        const tickDelta1m = (tickCumulatives[0].sub(tickCumulatives[1])).div(60);
        console.log("Tick change per second (1m):", tickDelta1m.toString());

        console.log("\nPrice movement in last 5 minutes:");
        const tickDelta5m = (tickCumulatives[0].sub(tickCumulatives[2])).div(300);
        console.log("Tick change per second (5m):", tickDelta5m.toString());
    } catch (error) {
        console.log("Could not fetch price movement:", error.message);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
