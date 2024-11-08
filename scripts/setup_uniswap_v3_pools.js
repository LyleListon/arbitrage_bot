const hre = require("hardhat");

// Uniswap V3 addresses on Sepolia
const ADDRESSES = {
    factory: "0x1F98431c8aD98523631AE4a59f267346ea31F984",
    router: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    nftManager: "0x1238536071E1c677A632429e3655c799b22cDA52",
    WETH: "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
    USDC: "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8",
    WBTC: "0x29f2D40B0605204364af54EC677bD022dA425d03"
};

// First, wrap ETH to get WETH
async function wrapETH(amount) {
    const weth = await hre.ethers.getContractAt(
        [
            "function deposit() external payable",
            "function balanceOf(address) external view returns (uint256)"
        ],
        ADDRESSES.WETH
    );

    console.log(`Wrapping ${hre.ethers.utils.formatEther(amount)} ETH to WETH...`);
    const tx = await weth.deposit({ value: amount });
    await tx.wait();
    
    const [signer] = await hre.ethers.getSigners();
    const balance = await weth.balanceOf(signer.address);
    console.log(`WETH balance: ${hre.ethers.utils.formatEther(balance)}`);
    
    return balance;
}

// Create a new pool if it doesn't exist
async function createPool(factory, token0, token1, fee) {
    try {
        console.log(`\nCreating pool for ${token0}/${token1} with ${fee/10000}% fee...`);
        
        // Check if pool exists
        const pool = await factory.getPool(token0, token1, fee);
        if (pool !== "0x0000000000000000000000000000000000000000") {
            console.log(`Pool already exists at ${pool}`);
            return pool;
        }
        
        // Create pool
        const tx = await factory.createPool(token0, token1, fee);
        const receipt = await tx.wait();
        
        // Get pool address from event logs
        const poolCreatedEvent = receipt.events.find(e => e.event === "PoolCreated");
        const poolAddress = poolCreatedEvent.args.pool;
        
        console.log(`Pool created at ${poolAddress}`);
        return poolAddress;
    } catch (error) {
        console.error(`Error creating pool: ${error.message}`);
        return null;
    }
}

async function main() {
    try {
        console.log("Setting up Uniswap V3 pools on Sepolia...");
        
        // Get contracts
        const factory = await hre.ethers.getContractAt(
            [
                "function createPool(address tokenA, address tokenB, uint24 fee) external returns (address pool)",
                "function getPool(address,address,uint24) external view returns (address)"
            ],
            ADDRESSES.factory
        );
        
        // Wrap some ETH
        const ethAmount = hre.ethers.utils.parseEther("0.2"); // 0.2 ETH
        await wrapETH(ethAmount);
        
        // Create WETH/USDC pool with 0.3% fee
        await createPool(factory, ADDRESSES.WETH, ADDRESSES.USDC, 3000);
        
        // Create WETH/WBTC pool with 0.3% fee
        await createPool(factory, ADDRESSES.WETH, ADDRESSES.WBTC, 3000);
        
        console.log("\nPool setup complete!");
        
    } catch (error) {
        console.error("Setup failed:", error);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
