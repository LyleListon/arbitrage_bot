const hre = require("hardhat");
const config = require("../dashboard/deploy_config.json");

async function verifyRouter(router, name) {
    try {
        console.log(`\nVerifying ${name}...`);
        console.log(`Address: ${router}`);
        
        // Create contract instance with minimal ABI to test basic functions
        const routerABI = [
            "function WETH() external pure returns (address)",
            "function factory() external pure returns (address)"
        ];
        
        const routerContract = new hre.ethers.Contract(
            router,
            routerABI,
            hre.ethers.provider
        );
        
        // Try to get WETH address
        try {
            const weth = await routerContract.WETH();
            console.log(`WETH address: ${weth}`);
        } catch (error) {
            console.log(`Error getting WETH: ${error.message}`);
        }
        
        // Try to get factory address
        try {
            const factory = await routerContract.factory();
            console.log(`Factory address: ${factory}`);
        } catch (error) {
            console.log(`Error getting factory: ${error.message}`);
        }
        
        // Verify contract code exists
        const code = await hre.ethers.provider.getCode(router);
        if (code === "0x") {
            console.log("WARNING: No contract code at this address!");
        } else {
            console.log(`Contract code length: ${(code.length - 2) / 2} bytes`);
        }
        
    } catch (error) {
        console.error(`Error verifying ${name}: ${error.message}`);
    }
}

async function main() {
    console.log("Verifying DEX routers on Sepolia...");
    
    // Verify Uniswap V2 Router
    await verifyRouter(
        config.dex.sepolia.uniswapV2Router,
        "Uniswap V2 Router"
    );
    
    // Verify Sushiswap Router
    await verifyRouter(
        config.dex.sepolia.sushiswapRouter,
        "Sushiswap Router"
    );
    
    // Verify Pancakeswap Router
    await verifyRouter(
        config.dex.sepolia.pancakeswapRouter,
        "Pancakeswap Router"
    );
    
    // Get network info
    const network = await hre.ethers.provider.getNetwork();
    console.log("\nNetwork Information:");
    console.log(`Chain ID: ${network.chainId}`);
    console.log(`Network Name: ${network.name}`);
    
    const block = await hre.ethers.provider.getBlock("latest");
    console.log(`Latest Block: ${block.number}`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
