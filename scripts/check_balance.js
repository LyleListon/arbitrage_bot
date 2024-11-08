const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const balance = await deployer.getBalance();
  console.log(`Deployer Address: ${deployer.address}`);
  console.log(`Balance: ${hre.ethers.utils.formatEther(balance)} ETH`);

  // Get latest block number
  const provider = deployer.provider;
  const blockNumber = await provider.getBlockNumber();
  console.log(`Current Block Number: ${blockNumber}`);

  // Get gas price
  const gasPrice = await provider.getGasPrice();
  console.log(`Current Gas Price: ${hre.ethers.utils.formatUnits(gasPrice, "gwei")} gwei`);

  // Get nonce
  const nonce = await provider.getTransactionCount(deployer.address);
  console.log(`Current Nonce: ${nonce}`);

  // Get chain ID
  const network = await provider.getNetwork();
  console.log(`Chain ID: ${network.chainId}`);
  console.log(`Network Name: ${network.name}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Error:", error);
    process.exit(1);
  });
