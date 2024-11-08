const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Checking Uniswap V2 pool details...");

    // Token addresses
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Uniswap V2 Factory and Router
    const factoryAddress = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f";
    const routerAddress = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";

    // Interfaces
    const factoryABI = [
        "function getPair(address tokenA, address tokenB) external view returns (address pair)"
    ];

    const pairABI = [
        "function token0() external view returns (address)",
        "function token1() external view returns (address)",
        "function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast)",
        "function price0CumulativeLast() external view returns (uint256)",
        "function price1CumulativeLast() external view returns (uint256)"
    ];

    // Get contracts
    const factory = await ethers.getContractAt(factoryABI, factoryAddress);

    try {
        // Get pair address
        console.log("\nChecking WETH-USDC pair...");
        const pairAddress = await factory.getPair(WETH, USDC);
        console.log("Pair address:", pairAddress);

        if (pairAddress === ethers.constants.AddressZero) {
            console.log("Pair does not exist");
            return;
        }

        // Get pair contract
        const pair = await ethers.getContractAt(pairABI, pairAddress);

        // Get tokens
        const token0 = await pair.token0();
        const token1 = await pair.token1();
        console.log("\nToken0:", token0);
        console.log("Token1:", token1);

        // Get reserves
        const reserves = await pair.getReserves();
        console.log("\nReserves:");
        if (token0.toLowerCase() === WETH.toLowerCase()) {
            console.log("WETH:", ethers.utils.formatEther(reserves.reserve0));
            console.log("USDC:", ethers.utils.formatUnits(reserves.reserve1, 6));
        } else {
            console.log("WETH:", ethers.utils.formatEther(reserves.reserve1));
            console.log("USDC:", ethers.utils.formatUnits(reserves.reserve0, 6));
        }

        // Get price
        const price0Cumulative = await pair.price0CumulativeLast();
        const price1Cumulative = await pair.price1CumulativeLast();
        console.log("\nPrice cumulatives:");
        console.log("Price0:", price0Cumulative.toString());
        console.log("Price1:", price1Cumulative.toString());

    } catch (error) {
        console.error("\nError checking pool:", error.message);
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
