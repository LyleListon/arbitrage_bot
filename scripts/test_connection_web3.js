const { Web3 } = require('web3');
require('dotenv').config();

async function testWeb3Connection() {
  console.log("Testing connection to Base network using web3.js...");
  
  try {
    const rpcUrl = process.env.MAINNET_RPC_URL || "https://base.publicnode.com";
    const web3 = new Web3(rpcUrl);
    console.log("Provider created for URL:", rpcUrl);

    // Test connection by getting block number
    console.log("Getting block number...");
    const blockNumber = await web3.eth.getBlockNumber();
    console.log(`Current block number: ${blockNumber}`);

    const account = web3.eth.accounts.privateKeyToAccount(process.env.PRIVATE_KEY);
    console.log(`Using account: ${account.address}`);

    // Get balance
    const balance = await web3.eth.getBalance(account.address);
    console.log(`Wallet balance: ${web3.utils.fromWei(balance, 'ether')} ETH`);

    // Get chain ID
    const chainId = await web3.eth.getChainId();
    console.log(`Chain ID: ${chainId}`);

    // Get gas price
    const gasPrice = await web3.eth.getGasPrice();
    console.log(`Current gas price: ${web3.utils.fromWei(gasPrice, 'gwei')} gwei`);

    console.log("All tests passed successfully!");
    process.exit(0);
  } catch (error) {
    console.error("Error during testing:", error.message);
    if (error.code) console.error("Error code:", error.code);
    process.exit(1);
  }
}

// Run test with timeout
const timeout = 10000; // 10 seconds
Promise.race([
  testWeb3Connection(),
  new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`Test timed out after ${timeout}ms`)), timeout)
  )
]).catch(error => {
  console.error("Connection test failed:", error.message);
  process.exit(1);
});