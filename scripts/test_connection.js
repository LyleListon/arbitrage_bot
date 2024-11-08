const hre = require("hardhat");
const { ethers } = require('ethers');

async function testRpcWithEthers() {
  console.log("Testing connection to Base network...");
  
  try {
    // Create provider
    const provider = new ethers.providers.JsonRpcProvider("https://base.publicnode.com");
    console.log("Provider created.");

    // Test connection by getting block number
    console.log("Getting block number...");
    const blockNumber = await provider.getBlockNumber();
    console.log(`Current block number: ${blockNumber}`);

    // Test private key
    const wallet = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
    console.log(`Using wallet address: ${wallet.address}`);

    // Get balance
    const balance = await wallet.getBalance();
    console.log(`Wallet balance: ${ethers.utils.formatEther(balance)} ETH`);

    // Get chain ID
    const network = await provider.getNetwork();
    console.log(`Chain ID: ${network.chainId}`);

    // Get gas price
    const gasPrice = await provider.getGasPrice();
    console.log(`Current gas price: ${ethers.utils.formatUnits(gasPrice, "gwei")} gwei`);

    console.log("All tests passed successfully!");
    return true;
  } catch (error) {
    console.error("Error during testing:", error.message);
    if (error.code) console.error("Error code:", error.code);
    return false;
  }
}

// Run with timeout
const timeout = 10000; // 10 seconds
Promise.race([
  testRpcWithEthers(),
  new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`Test timed out after ${timeout}ms`)), timeout)
  )
])
.then((success) => {
  if (success) {
    console.log("Connection test completed successfully");
  } else {
    console.error("Connection test failed");
  }
  process.exit(success ? 0 : 1);
})
.catch((error) => {
  console.error("Connection test failed:", error.message);
  process.exit(1);
});