// Deployment script for ArbitrageBot
const hre = require("hardhat");

async function main() {
  console.log("Deploying ArbitrageBot to Sepolia...");

  // Deploy PriceFeedRegistry first
  const PriceFeedRegistry = await hre.ethers.getContractFactory("PriceFeedRegistry");
  const priceFeedRegistry = await PriceFeedRegistry.deploy();
  await priceFeedRegistry.deployed();
  console.log("PriceFeedRegistry deployed to:", priceFeedRegistry.address);

  // Deploy DEXRegistry
  const DEXRegistry = await hre.ethers.getContractFactory("DEXRegistry");
  const dexRegistry = await DEXRegistry.deploy();
  await dexRegistry.deployed();
  console.log("DEXRegistry deployed to:", dexRegistry.address);

  // Deploy ArbitrageBot with constructor parameters
  const ArbitrageBot = await hre.ethers.getContractFactory("ArbitrageBot");
  const arbitrageBot = await ArbitrageBot.deploy(
    300, // 3% minimum profit (in basis points)
    ethers.utils.parseEther("10"), // 10 ETH max trade size
    3600, // 1 hour emergency withdrawal delay
    priceFeedRegistry.address,
    dexRegistry.address
  );
  await arbitrageBot.deployed();
  console.log("ArbitrageBot deployed to:", arbitrageBot.address);

  // Verify contracts on Etherscan
  console.log("Verifying contracts on Etherscan...");

  await hre.run("verify:verify", {
    address: priceFeedRegistry.address,
    constructorArguments: [],
  });

  await hre.run("verify:verify", {
    address: dexRegistry.address,
    constructorArguments: [],
  });

  await hre.run("verify:verify", {
    address: arbitrageBot.address,
    constructorArguments: [
      300,
      ethers.utils.parseEther("10"),
      3600,
      priceFeedRegistry.address,
      dexRegistry.address
    ],
  });

  console.log("Deployment and verification complete!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
