const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function getFactoryAddress(router) {
    try {
        const routerContract = await hre.ethers.getContractAt("contracts/interfaces/IUniswapV2Router.sol:IUniswapV2Router", router);
        return await routerContract.factory();
    } catch (error) {
        console.error(`Error getting factory address: ${error.message}`);
        return null;
    }
}

async function checkPair(factoryAddress, token0, token1, dexName) {
    try {
        const factory = await hre.ethers.getContractAt("IUniswapV2Factory", factoryAddress);
        const pairAddress = await factory.getPair(token0, token1);
        
        if (pairAddress === "0x0000000000000000000000000000000000000000") {
            console.log(`${dexName}: Pair does not exist`);
            return;
        }
        
        const pair = await hre.ethers.getContractAt("IUniswapV2Pair", pairAddress);
        const [reserve0, reserve1] = await pair.getReserves();
        
        console.log(`${dexName}:`);
        console.log(`- Pair Address: ${pairAddress}`);
        console.log(`- Reserve0: ${hre.ethers.utils.formatEther(reserve0)}`);
        console.log(`- Reserve1: ${hre.ethers.utils.formatEther(reserve1)}`);
    } catch (error) {
        console.error(`Error checking pair: ${error.message}`);
    }
}

async function main() {
    try {
        console.log("Checking liquidity pairs...");
        
        const WETH = config.tokens.sepolia.WETH;
        const USDC = config.tokens.sepolia.USDC;
        const WBTC = config.tokens.sepolia.WBTC;
        
        // Get factory addresses
        console.log("\nGetting factory addresses...");
        const uniFactory = await getFactoryAddress(config.dex.sepolia.uniswapV2Router);
        const sushiFactory = await getFactoryAddress(config.dex.sepolia.sushiswapRouter);
        
        console.log(`Uniswap V2 Factory: ${uniFactory}`);
        console.log(`Sushiswap Factory: ${sushiFactory}`);
        
        // Check ETH/USDC pairs
        console.log("\nChecking ETH/USDC pairs...");
        await checkPair(uniFactory, WETH, USDC, "Uniswap V2");
        await checkPair(sushiFactory, WETH, USDC, "Sushiswap");
        
        // Check ETH/WBTC pairs
        console.log("\nChecking ETH/WBTC pairs...");
        await checkPair(uniFactory, WETH, WBTC, "Uniswap V2");
        await checkPair(sushiFactory, WETH, WBTC, "Sushiswap");
        
    } catch (error) {
        console.error("Error checking pairs:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
