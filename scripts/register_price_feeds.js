// Script to register price feeds in the PriceFeedRegistry
const { ethers } = require("hardhat");

async function main() {
    console.log("Registering price feeds...");

    // Get the PriceFeedRegistry contract
    const priceFeedRegistry = await ethers.getContractAt(
        "PriceFeedRegistry",
        "0xab0c8abc894B9bc7Bcb22Da41DCF5f9f93A55b29"
    );

    // Token addresses from config
    const WETH = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9";
    const WBTC = "0x29f2D40B0605204364af54EC677bD022dA425d03";
    const USDC = "0xda9d4f9b69ac6C22e444eD9aF0CfC043b7a7f53f";

    // Chainlink feed addresses from config
    const ETH_USD_FEED = "0x694AA1769357215DE4FAC081bf1f309aDC325306";
    const BTC_USD_FEED = "0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43";

    // Default stale threshold (1 hour)
    const STALE_THRESHOLD = 3600;

    // Register ETH/USDC price feed
    console.log("Registering ETH/USDC price feed...");
    await priceFeedRegistry.registerPriceFeed(
        WETH,
        USDC,
        ETH_USD_FEED,
        STALE_THRESHOLD
    );

    // Register WBTC/USDC price feed
    console.log("Registering WBTC/USDC price feed...");
    await priceFeedRegistry.registerPriceFeed(
        WBTC,
        USDC,
        BTC_USD_FEED,
        STALE_THRESHOLD
    );

    console.log("Price feeds registered successfully!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
