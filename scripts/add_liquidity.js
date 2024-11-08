const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Adding liquidity to WETH-USDC pool on Sepolia...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Uniswap V3 contracts
    const routerAddress = "0xE592427A0AEce92De3Edee1F18E0157C05861564";
    const poolAddress = "0x6Ce0896eAE6D4BD668fDe41BB784548fb8F59b50";

    // Router interface
    const routerABI = [
        "function exactInputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountIn, uint256 amountOutMinimum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountOut)",
        "function exactOutputSingle((address tokenIn, address tokenOut, uint24 fee, address recipient, uint256 deadline, uint256 amountOut, uint256 amountInMaximum, uint160 sqrtPriceLimitX96)) external payable returns (uint256 amountIn)",
        "function mint((address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, uint256 amount0Desired, uint256 amount1Desired, uint256 amount0Min, uint256 amount1Min, address recipient, uint256 deadline)) external payable returns (uint256 amount0, uint256 amount1, uint256 liquidity)"
    ];

    // WETH interface for wrapping ETH
    const wethABI = [
        "function deposit() external payable",
        "function approve(address spender, uint256 amount) external returns (bool)"
    ];

    // USDC interface
    const usdcABI = [
        "function approve(address spender, uint256 amount) external returns (bool)",
        "function balanceOf(address account) external view returns (uint256)"
    ];

    // Get contracts
    const router = await ethers.getContractAt(routerABI, routerAddress);
    const weth = await ethers.getContractAt(wethABI, WETH);
    const usdc = await ethers.getContractAt(usdcABI, USDC);

    // Get signer
    const [signer] = await ethers.getSigners();
    console.log("Using signer:", signer.address);

    try {
        // Using 9 USDC (leaving 1 USDC as buffer)
        const usdcAmount = ethers.utils.parseUnits("9", 6); // 9 USDC
        // Calculate proportional ETH amount (at 2000 USDC/ETH price)
        const wethAmount = ethers.utils.parseEther("0.0045"); // 9/2000 ETH

        // First wrap ETH
        console.log("\nWrapping", ethers.utils.formatEther(wethAmount), "ETH...");
        const wrapTx = await weth.deposit({ value: wethAmount });
        await wrapTx.wait();
        console.log("ETH wrapped successfully!");

        // Approve router to spend WETH
        console.log("\nApproving WETH spend...");
        const wethApproveTx = await weth.approve(routerAddress, wethAmount);
        await wethApproveTx.wait();
        console.log("WETH approved!");

        // Approve router to spend USDC
        console.log("\nApproving USDC spend...");
        const usdcApproveTx = await usdc.approve(routerAddress, usdcAmount);
        await usdcApproveTx.wait();
        console.log("USDC approved!");

        // Add liquidity
        console.log("\nAdding liquidity...");
        console.log("WETH amount:", ethers.utils.formatEther(wethAmount), "WETH");
        console.log("USDC amount:", ethers.utils.formatUnits(usdcAmount, 6), "USDC");

        // Calculate ticks for price range (±5% around current price)
        const currentTick = 180674; // From pool state
        const tickSpacing = 60; // For 0.3% fee tier
        const tickRange = 100; // About ±5% price range
        const tickLower = Math.floor((currentTick - tickRange) / tickSpacing) * tickSpacing;
        const tickUpper = Math.floor((currentTick + tickRange) / tickSpacing) * tickSpacing;

        const mintParams = {
            token0: USDC, // Token0 is USDC
            token1: WETH, // Token1 is WETH
            fee: 3000,
            tickLower,
            tickUpper,
            amount0Desired: usdcAmount,
            amount1Desired: wethAmount,
            amount0Min: 0,
            amount1Min: 0,
            recipient: signer.address,
            deadline: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
        };

        const addLiquidityTx = await router.mint(mintParams);
        await addLiquidityTx.wait();
        console.log("Liquidity added successfully!");

        // Get pool state after adding liquidity
        const poolABI = [
            "function liquidity() external view returns (uint128)",
            "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)"
        ];
        const pool = await ethers.getContractAt(poolABI, poolAddress);

        const liquidity = await pool.liquidity();
        const slot0 = await pool.slot0();

        console.log("\nPool state after adding liquidity:");
        console.log("Liquidity:", liquidity.toString());
        console.log("Current tick:", slot0.tick.toString());
        console.log("Pool unlocked:", slot0.unlocked);

    } catch (error) {
        console.error("\nError adding liquidity:", error.message);
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
