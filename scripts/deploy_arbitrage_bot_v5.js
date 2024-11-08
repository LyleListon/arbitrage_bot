const hre = require("hardhat");

async function main() {
  console.log("Deploying ArbitrageBotV5...");

  // Deploy parameters
  const minProfitBasisPoints = 50; // 0.5%
  const maxTradeSize = ethers.utils.parseEther("10"); // 10 ETH
  const emergencyWithdrawalDelay = 3600; // 1 hour
  const maxGasPrice = ethers.utils.parseUnits("100", "gwei"); // 100 gwei
  const circuitBreakerThreshold = 100; // Stop after 100 trades
  const poolAddressProvider = process.env.AAVE_POOL_PROVIDER;

  // Deploy contract
  const ArbitrageBotV5 = await hre.ethers.getContractFactory("ArbitrageBotV5");
  const bot = await ArbitrageBotV5.deploy(
    minProfitBasisPoints,
    maxTradeSize,
    emergencyWithdrawalDelay,
    maxGasPrice,
    circuitBreakerThreshold,
    poolAddressProvider
  );

  await bot.deployed();

  console.log("ArbitrageBotV5 deployed to:", bot.address);
  console.log("Configuration:");
  console.log("- Min Profit Basis Points:", minProfitBasisPoints);
  console.log("- Max Trade Size:", ethers.utils.formatEther(maxTradeSize), "ETH");
  console.log("- Emergency Withdrawal Delay:", emergencyWithdrawalDelay, "seconds");
  console.log("- Max Gas Price:", ethers.utils.formatUnits(maxGasPrice, "gwei"), "gwei");
  console.log("- Circuit Breaker Threshold:", circuitBreakerThreshold, "trades");
  console.log("- Pool Address Provider:", poolAddressProvider);

  // Verify contract
  if (process.env.ETHERSCAN_API_KEY) {
    console.log("Waiting for contract verification...");
    await bot.deployTransaction.wait(6); // Wait for 6 block confirmations
    
    try {
      await hre.run("verify:verify", {
        address: bot.address,
        constructorArguments: [
          minProfitBasisPoints,
          maxTradeSize,
          emergencyWithdrawalDelay,
          maxGasPrice,
          circuitBreakerThreshold,
          poolAddressProvider
        ],
      });
      console.log("Contract verified successfully");
    } catch (error) {
      console.error("Error verifying contract:", error);
    }
  }

  // Save deployment info
  const fs = require('fs');
  const deploymentInfo = {
    address: bot.address,
    network: hre.network.name,
    timestamp: new Date().toISOString(),
    constructorArgs: {
      minProfitBasisPoints,
      maxTradeSize: maxTradeSize.toString(),
      emergencyWithdrawalDelay,
      maxGasPrice: maxGasPrice.toString(),
      circuitBreakerThreshold,
      poolAddressProvider
    }
  };

  const deploymentPath = './deployments';
  if (!fs.existsSync(deploymentPath)) {
    fs.mkdirSync(deploymentPath);
  }

  fs.writeFileSync(
    `${deploymentPath}/ArbitrageBotV5_${hre.network.name}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );

  // Copy ABI to dashboard directory
  const artifactPath = 'artifacts/contracts/ArbitrageBotV5.sol/ArbitrageBotV5.json';
  const dashboardAbiPath = 'dashboard/abi';
  
  if (!fs.existsSync(dashboardAbiPath)) {
    fs.mkdirSync(dashboardAbiPath, { recursive: true });
  }

  fs.copyFileSync(artifactPath, `${dashboardAbiPath}/ArbitrageBotV5.json`);

  console.log(`Deployment info saved to: ${deploymentPath}/ArbitrageBotV5_${hre.network.name}.json`);
  console.log(`ABI copied to: ${dashboardAbiPath}/ArbitrageBotV5.json`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
