const hre = require("hardhat");

async function main() {
  console.log("Deploying ArbitrageBotV5...");

  // Constructor parameters
  const minProfitBasisPoints = 50; // 0.5%
  const maxTradeSize = ethers.utils.parseEther("10"); // 10 ETH max trade size
  const emergencyWithdrawalDelay = 3600; // 1 hour
  const maxGasPrice = ethers.utils.parseUnits("100", "gwei"); // 100 gwei
  const circuitBreakerThreshold = 100; // 100 trades
  const aavePoolProvider = process.env.AAVE_POOL_PROVIDER;

  const ArbitrageBotV5 = await hre.ethers.getContractFactory("ArbitrageBotV5");
  const bot = await ArbitrageBotV5.deploy(
    minProfitBasisPoints,
    maxTradeSize,
    emergencyWithdrawalDelay,
    maxGasPrice,
    circuitBreakerThreshold,
    aavePoolProvider
  );

  await bot.deployed();

  console.log("ArbitrageBotV5 deployed to:", bot.address);
  
  // Wait for a few block confirmations
  console.log("Waiting for block confirmations...");
  await bot.deployTransaction.wait(5);

  // Verify the contract
  console.log("Verifying contract on Etherscan...");
  await hre.run("verify:verify", {
    address: bot.address,
    constructorArguments: [
      minProfitBasisPoints,
      maxTradeSize,
      emergencyWithdrawalDelay,
      maxGasPrice,
      circuitBreakerThreshold,
      aavePoolProvider
    ],
  });

  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    network: hre.network.name,
    address: bot.address,
    timestamp: new Date().toISOString(),
    constructor: {
      minProfitBasisPoints,
      maxTradeSize: maxTradeSize.toString(),
      emergencyWithdrawalDelay,
      maxGasPrice: maxGasPrice.toString(),
      circuitBreakerThreshold,
      aavePoolProvider
    }
  };

  fs.writeFileSync(
    "deployments/ArbitrageBotV5_deployment.json",
    JSON.stringify(deploymentInfo, null, 2)
  );
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
