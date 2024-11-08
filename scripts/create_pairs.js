const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function createPair(factoryAddress, token0, token1, dexName) {
    try {
        const factory = await hre.ethers.getContractAt("IUniswapV2Factory", factoryAddress);
        
        // Check if pair already exists
        const existingPair = await factory.getPair(token0, token1);
        if (existingPair !== "0x0000000000000000000000000000000000000000") {
            console.log(`${dexName}: Pair already exists at ${existingPair}`);
            return existingPair;
        }
        
        // Create new pair
        console.log(`${dexName}: Creating new pair...`);
        const tx = await factory.createPair(token0, token1);
        await tx.wait();
        
        // Get the new pair address
        const pairAddress = await factory.getPair(token0, token1);
        console.log(`${dexName}: Pair created at ${pairAddress}`);
        
        return pairAddress;
    } catch (error) {
        console.error(`${dexName}: Error creating pair: ${error.message}`);
        return null;
    }
}

async function getFactoryAddress(router) {
    try {
        const routerContract = await hre.ethers.getContractAt("contracts/interfaces/IUniswapV2Router.sol:IUniswapV2Router", router);
        return await routerContract.factory();
    } catch (error) {
        console.error(`Error getting factory address: ${error.message}`);
        return null;
    }
}

async function main() {
    try {
        console.log("Creating liquidity pairs...");
        
        const WETH = config.tokens.sepolia.WETH;
        const USDC = config.tokens.sepolia.USDC;
        const WBTC = config.tokens.sepolia.WBTC;
        
        // Get factory addresses
        console.log("\nGetting factory addresses...");
        const uniFactory = await getFactoryAddress(config.dex.sepolia.uniswapV2Router);
        const sushiFactory = await getFactoryAddress(config.dex.sepolia.sushiswapRouter);
        
        console.log(`Uniswap V2 Factory: ${uniFactory}`);
        console.log(`Sushiswap Factory: ${sushiFactory}`);
        
        // Create ETH/USDC pairs
        console.log("\nCreating ETH/USDC pairs...");
        await createPair(uniFactory, WETH, USDC, "Uniswap V2");
        await createPair(sushiFactory, WETH, USDC, "Sushiswap");
        
        // Create ETH/WBTC pairs
        console.log("\nCreating ETH/WBTC pairs...");
        await createPair(uniFactory, WETH, WBTC, "Uniswap V2");
        await createPair(sushiFactory, WETH, WBTC, "Sushiswap");
        
        console.log("\nPair creation complete!");
        
    } catch (error) {
        console.error("Error creating pairs:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
