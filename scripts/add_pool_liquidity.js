const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Adding liquidity to Uniswap V3 WETH-USDC pool...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Pool and position manager addresses
    const poolAddress = "0x6Ce0896eAE6D4BD668fDe41BB784548fb8F59b50";
    const positionManagerAddress = "0x1238536071E1c677A632429e3655c799b22cDA52";

    // Interfaces
    const positionManagerABI = [
        "function mint((address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, uint256 amount0Desired, uint256 amount1Desired, uint256 amount0Min, uint256 amount1Min, address recipient, uint256 deadline)) external payable returns (uint256 tokenId, uint128 liquidity, uint256 amount0, uint256 amount1)",
        "function positions(uint256 tokenId) external view returns (uint96 nonce, address operator, address token0, address token1, uint24 fee, int24 tickLower, int24 tickUpper, uint128 liquidity, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, uint128 tokensOwed0, uint128 tokensOwed1)"
    ];

    const poolABI = [
        "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)",
        "function token0() external view returns (address)",
        "function token1() external view returns (address)"
    ];

    const erc20ABI = [
        "function approve(address spender, uint256 amount) external returns (bool)",
        "function balanceOf(address account) external view returns (uint256)",
        "function allowance(address owner, address spender) external view returns (uint256)"
    ];

    // Get contracts
    const positionManager = await ethers.getContractAt(positionManagerABI, positionManagerAddress);
    const pool = await ethers.getContractAt(poolABI, poolAddress);
    const weth = await ethers.getContractAt(erc20ABI, WETH);
    const usdc = await ethers.getContractAt(erc20ABI, USDC);

    // Get signer
    const [signer] = await ethers.getSigners();
    console.log("Using signer:", signer.address);

    try {
        // Check initial balances
        const wethBalance = await weth.balanceOf(signer.address);
        const usdcBalance = await usdc.balanceOf(signer.address);
        console.log("\nInitial balances:");
        console.log("WETH:", ethers.utils.formatEther(wethBalance));
        console.log("USDC:", ethers.utils.formatUnits(usdcBalance, 6));

        // Get current pool state
        const slot0 = await pool.slot0();
        const currentTick = slot0.tick;
        console.log("\nCurrent pool tick:", currentTick);

        // Calculate current price
        const Q96 = ethers.BigNumber.from('2').pow(96);
        const sqrtPriceX96 = slot0.sqrtPriceX96;
        const priceX96 = sqrtPriceX96.mul(sqrtPriceX96).div(Q96);
        const price = priceX96.mul(ethers.utils.parseUnits('1', 6)).div(ethers.utils.parseEther('1'));
        console.log("Current price:", ethers.utils.formatUnits(price, 6), "USDC per ETH");

        // Calculate tick range (±2.5% around current price)
        const tickSpacing = 60; // 0.3% fee tier
        const tickRange = 50; // About ±2.5% price range
        const tickLower = Math.floor((currentTick - tickRange) / tickSpacing) * tickSpacing;
        const tickUpper = Math.floor((currentTick + tickRange) / tickSpacing) * tickSpacing;

        console.log("Adding liquidity in tick range:", tickLower, "to", tickUpper);

        // Amount to add (0.05 WETH and equivalent USDC based on current price)
        const wethAmount = ethers.utils.parseEther("0.05");
        const usdcAmount = ethers.utils.parseUnits("9", 6); // Using most of our USDC

        // Approve tokens
        console.log("\nApproving tokens...");
        if ((await weth.allowance(signer.address, positionManagerAddress)).lt(wethAmount)) {
            const wethApproveTx = await weth.approve(positionManagerAddress, ethers.constants.MaxUint256);
            await wethApproveTx.wait();
            console.log("WETH approved");
        }
        if ((await usdc.allowance(signer.address, positionManagerAddress)).lt(usdcAmount)) {
            const usdcApproveTx = await usdc.approve(positionManagerAddress, ethers.constants.MaxUint256);
            await usdcApproveTx.wait();
            console.log("USDC approved");
        }

        // Prepare mint parameters
        const params = {
            token0: USDC, // USDC is token0
            token1: WETH, // WETH is token1
            fee: 3000,
            tickLower,
            tickUpper,
            amount0Desired: usdcAmount,
            amount1Desired: wethAmount,
            amount0Min: 0, // No minimum to allow for slippage
            amount1Min: 0, // No minimum to allow for slippage
            recipient: signer.address,
            deadline: Math.floor(Date.now() / 1000) + 3600
        };

        // Add liquidity
        console.log("\nAdding liquidity...");
        console.log("WETH amount:", ethers.utils.formatEther(wethAmount));
        console.log("USDC amount:", ethers.utils.formatUnits(usdcAmount, 6));

        const mintTx = await positionManager.mint(params, { gasLimit: 1000000 }); // Set explicit gas limit
        console.log("Waiting for transaction...");
        const receipt = await mintTx.wait();
        console.log("Transaction hash:", receipt.transactionHash);

        // Get position ID from logs
        const mintEvent = receipt.events?.find(e => e.event === "IncreaseLiquidity");
        if (mintEvent) {
            const tokenId = mintEvent.args.tokenId;
            console.log("\nPosition created with token ID:", tokenId.toString());

            // Get position details
            const position = await positionManager.positions(tokenId);
            console.log("\nPosition details:");
            console.log("Liquidity:", position.liquidity.toString());
            console.log("Tick range:", position.tickLower, "to", position.tickUpper);
        }

        // Check final balances
        const finalWethBalance = await weth.balanceOf(signer.address);
        const finalUsdcBalance = await usdc.balanceOf(signer.address);

        console.log("\nFinal balances:");
        console.log("WETH:", ethers.utils.formatEther(finalWethBalance));
        console.log("USDC:", ethers.utils.formatUnits(finalUsdcBalance, 6));

        // Calculate and display changes
        const wethChange = wethBalance.sub(finalWethBalance);
        const usdcChange = usdcBalance.sub(finalUsdcBalance);
        console.log("\nBalance changes:");
        console.log("WETH:", ethers.utils.formatEther(wethChange));
        console.log("USDC:", ethers.utils.formatUnits(usdcChange, 6));

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
