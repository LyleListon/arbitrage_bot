const hre = require("hardhat");
const { ethers } = require("hardhat");

// Goerli addresses for reference
const GOERLI = {
    // Core contracts
    factory: '0x1F98431c8aD98523631AE4a59f267346ea31F984',
    router: '0xE592427A0AEce92De3Edee1F18E0157C05861564',
    quoter: '0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6',

    // Tokens
    WETH: '0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6',
    USDC: '0x07865c6e87b9f70255377e024ace6630c1eaa37f',

    // Known pools
    'WETH/USDC-0.3%': '0x6337B3caf9C5236c7f3D1694410776119eDaF9FA',

    // Useful contracts
    positionManager: '0xC36442b4a4522E871399CD717aBDD847Ab11FE88',
    swapRouter02: '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45'
};

async function main() {
    console.log("Goerli Network Setup Guide");
    console.log("==========================");

    console.log("\nCore Contracts:");
    console.log("Factory:", GOERLI.factory);
    console.log("Router:", GOERLI.router);
    console.log("Router02:", GOERLI.swapRouter02);
    console.log("Quoter:", GOERLI.quoter);
    console.log("Position Manager:", GOERLI.positionManager);

    console.log("\nTokens:");
    console.log("WETH:", GOERLI.WETH);
    console.log("USDC:", GOERLI.USDC);

    console.log("\nKnown Pools:");
    console.log("WETH/USDC 0.3%:", GOERLI['WETH/USDC-0.3%']);

    console.log("\nMigration Steps:");
    console.log("1. Update hardhat.config.js with Goerli network");
    console.log("2. Get Goerli ETH from faucet");
    console.log("3. Wrap ETH to WETH");
    console.log("4. Get test USDC");
    console.log("5. Test basic operations before full migration");

    console.log("\nHardhat Config Example:");
    console.log(`
networks: {
    goerli: {
        url: 'https://goerli.infura.io/v3/YOUR-PROJECT-ID',
        accounts: [process.env.PRIVATE_KEY],
        chainId: 5
    }
}`);

    console.log("\nUseful Commands:");
    console.log("- Check balance: npx hardhat run scripts/check_balances.js --network goerli");
    console.log("- Wrap ETH: npx hardhat run scripts/wrap_eth.js --network goerli");
    console.log("- Add liquidity: npx hardhat run scripts/add_pool_liquidity.js --network goerli");
    console.log("- Test swap: npx hardhat run scripts/swap_weth_to_usdc.js --network goerli");

    console.log("\nFaucets:");
    console.log("- Goerli ETH: https://goerlifaucet.com/");
    console.log("- Test USDC: Check Compound or Aave faucets");

    console.log("\nNext Steps:");
    console.log("1. Update all contract addresses in config files");
    console.log("2. Test each script individually on Goerli");
    console.log("3. Monitor gas costs and transaction times");
    console.log("4. Document any differences in behavior");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
