const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
    console.log("Checking DEX Registry status...");

    // Get the DEX Registry contract
    const registryAddress = "0xc6BbdD9063A9d247F21BE0C71aAbd95b1C312e8B";
    console.log(`DEX Registry Address: ${registryAddress}`);

    const registry = await ethers.getContractAt("DEXRegistry", registryAddress);

    console.log("\nFetching active DEXes...");
    const activeDEXes = await registry.getActiveDEXes();

    console.log(`Found ${activeDEXes.length} active DEXes\n`);

    for (const dex of activeDEXes) {
        const info = await registry.getDEXInfo(dex);
        console.log(`DEX Address: ${dex}`);
        console.log(`Protocol: ${info[0]}`); // protocol
        console.log(`Max Slippage: ${info[1]}`); // maxSlippage
        console.log(`Active: ${info[2]}`); // isActive
        console.log(`Gas Overhead: ${info[3]}`); // overhead
        console.log("------------------------");
    }

    // Check specific token pair support
    const WETH = "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14";
    const USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    console.log("\nChecking WETH/USDC pair support:");
    for (const dex of activeDEXes) {
        const supported = await registry.isPairSupported(dex, WETH, USDC);
        if (supported) {
            const info = await registry.getDEXInfo(dex);
            console.log(`DEX ${dex} (${info[0]}) supports WETH/USDC trading`);
        }
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
