const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Checking swap quote on Uniswap V3...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Quoter V2 address
    const quoterAddress = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e";

    // Interfaces
    const quoterABI = [
        "function quoteExactInputSingle(address tokenIn, address tokenOut, uint24 fee, uint256 amountIn, uint160 sqrtPriceLimitX96) external returns (uint256 amountOut, uint160 sqrtPriceX96After, uint32 initializedTicksCrossed, uint256 gasEstimate)",
        "function quote(bytes memory path, uint256 amountIn) external returns (uint256 amountOut, uint160[] memory sqrtPriceX96AfterList, uint32[] memory initializedTicksCrossedList, uint256 gasEstimate)"
    ];

    // Get contracts
    const quoter = await ethers.getContractAt(quoterABI, quoterAddress);

    try {
        // Amount to quote (0.001 WETH)
        const amountIn = ethers.utils.parseEther("0.001");
        console.log("\nGetting quote for:", ethers.utils.formatEther(amountIn), "WETH");

        // Try different fee tiers
        const feeTiers = [500, 3000, 10000]; // 0.05%, 0.3%, 1%

        for (const fee of feeTiers) {
            console.log(`\nChecking ${fee/10000}% fee tier...`);
            try {
                const quote = await quoter.callStatic.quoteExactInputSingle(
                    WETH,
                    USDC,
                    fee,
                    amountIn,
                    0
                );

                console.log("Expected USDC output:", ethers.utils.formatUnits(quote.amountOut, 6));
                console.log("Gas estimate:", quote.gasEstimate.toString());
                console.log("Ticks crossed:", quote.initializedTicksCrossed.toString());

                // Calculate price impact
                const expectedPrice = quote.amountOut.mul(ethers.utils.parseEther("1")).div(amountIn);
                console.log("Effective price:", ethers.utils.formatUnits(expectedPrice, 6), "USDC per ETH");

            } catch (error) {
                console.log("Quote failed:", error.message);
            }
        }

        // Try path-based quote
        console.log("\nTrying path-based quote...");
        const path = ethers.utils.solidityPack(
            ['address', 'uint24', 'address'],
            [WETH, 3000, USDC]
        );

        try {
            const pathQuote = await quoter.callStatic.quote(path, amountIn);
            console.log("\nPath quote results:");
            console.log("Expected USDC output:", ethers.utils.formatUnits(pathQuote.amountOut, 6));
            console.log("Gas estimate:", pathQuote.gasEstimate.toString());
        } catch (error) {
            console.log("Path quote failed:", error.message);
        }

    } catch (error) {
        console.error("\nError getting quote:", error.message);
        if (error.error) {
            console.error("\nError details:", error.error);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
