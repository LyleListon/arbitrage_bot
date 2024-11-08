const hre = require("hardhat");

// Uniswap V3 addresses on Sepolia
const ADDRESSES = {
    factory: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    positionManager: "0x1238536071E1c677A632429e3655c799b22cDA52",
    WETH: "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    USDC: "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
};

const FACTORY_ABI = [
    "event PoolCreated(address indexed token0, address indexed token1, uint24 indexed fee, int24 tickSpacing, address pool)",
    "function createPool(address tokenA, address tokenB, uint24 fee) external returns (address pool)",
    "function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool)"
];

const POOL_ABI = [
    "function initialize(uint160 sqrtPriceX96) external",
    "function token0() external view returns (address)",
    "function token1() external view returns (address)",
    "function fee() external view returns (uint24)",
    "function tickSpacing() external view returns (int24)",
    "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)"
];

async function getPoolAddress(factory, token0, token1, fee) {
    // Try to get existing pool
    const pool = await factory.getPool(token0, token1, fee);
    if (pool !== "0x0000000000000000000000000000000000000000") {
        return pool;
    }
    
    // Create new pool
    console.log("Creating new pool...");
    const tx = await factory.createPool(token0, token1, fee, { gasLimit: 5000000 });
    console.log(`Transaction hash: ${tx.hash}`);
    await tx.wait();
    
    // Get pool address
    return await factory.getPool(token0, token1, fee);
}

async function main() {
    try {
        console.log("Setting up WETH/USDC pool on Uniswap V3...");
        
        // Get factory contract
        const factory = await hre.ethers.getContractAt(FACTORY_ABI, ADDRESSES.factory);
        
        // Get or create pool
        console.log("\nGetting/creating pool...");
        const poolAddress = await getPoolAddress(
            factory,
            ADDRESSES.WETH,
            ADDRESSES.USDC,
            3000 // 0.3% fee
        );
        
        if (poolAddress === "0x0000000000000000000000000000000000000000") {
            throw new Error("Failed to get or create pool");
        }
        
        console.log(`Pool address: ${poolAddress}`);
        
        // Get pool contract
        const pool = await hre.ethers.getContractAt(POOL_ABI, poolAddress);
        
        // Check if pool needs initialization
        try {
            const [sqrtPriceX96] = await pool.slot0();
            console.log("Pool already initialized");
            console.log(`Current sqrt price: ${sqrtPriceX96.toString()}`);
        } catch (error) {
            // Pool needs initialization
            console.log("\nInitializing pool...");
            
            // Price: 1 ETH = 2600 USDC
            // sqrt(2600) * 2^96
            const sqrtPriceX96 = "3323406039105959588437001438";
            
            const initTx = await pool.initialize(sqrtPriceX96, { gasLimit: 1000000 });
            await initTx.wait();
            console.log("Pool initialized successfully");
        }
        
        // Verify pool setup
        const token0 = await pool.token0();
        const token1 = await pool.token1();
        const fee = await pool.fee();
        const tickSpacing = await pool.tickSpacing();
        
        console.log("\nPool details:");
        console.log(`Token0: ${token0}`);
        console.log(`Token1: ${token1}`);
        console.log(`Fee: ${fee}`);
        console.log(`Tick spacing: ${tickSpacing}`);
        
        console.log("\nPool setup complete!");
        
    } catch (error) {
        console.error("Failed to setup pool:", error);
        
        // Additional error details
        if (error.transaction) {
            console.log("\nTransaction details:");
            console.log(`Hash: ${error.transaction.hash}`);
            console.log(`To: ${error.transaction.to}`);
            console.log(`From: ${error.transaction.from}`);
            console.log(`Data: ${error.transaction.data}`);
        }
        
        if (error.receipt) {
            console.log("\nTransaction receipt:");
            console.log(`Status: ${error.receipt.status}`);
            console.log(`Gas used: ${error.receipt.gasUsed.toString()}`);
            console.log(`Block number: ${error.receipt.blockNumber}`);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
