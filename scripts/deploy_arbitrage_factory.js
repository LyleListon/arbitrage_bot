const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

// Validate environment variables
function validateEnv() {
  const required = [
    'SEPOLIA_RPC_URL',
    'PRIVATE_KEY',
    'DEFAULT_MIN_PROFIT_BASIS_POINTS',
    'DEFAULT_MAX_TRADE_SIZE',
    'EMERGENCY_WITHDRAWAL_DELAY'
  ];

  const missing = required.filter(key => !process.env[key]);
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }
}

async function getGasPrice() {
  const maxGwei = process.env.MAX_GAS_PRICE_GWEI || "50";
  const provider = hre.ethers.provider;
  const currentGasPrice = await provider.getGasPrice();
  const maxGasPrice = hre.ethers.utils.parseUnits(maxGwei, "gwei");

  return currentGasPrice.gt(maxGasPrice) ? maxGasPrice : currentGasPrice;
}

async function ensureDeploymentDir() {
  const deployDir = path.join(__dirname, "../deployments");
  if (!fs.existsSync(deployDir)) {
    fs.mkdirSync(deployDir);
  }
}

async function main() {
  try {
    // Validate environment
    validateEnv();
    await ensureDeploymentDir();

    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);

    const balance = await deployer.getBalance();
    console.log("Account balance:", hre.ethers.utils.formatEther(balance), "ETH");

    // Get current gas price
    const gasPrice = await getGasPrice();
    console.log("Current gas price:", hre.ethers.utils.formatUnits(gasPrice, "gwei"), "gwei");

    console.log("\nDeploying ArbitrageFactory...");

    // Deploy ArbitrageFactory with dynamic gas settings
    const ArbitrageFactory = await hre.ethers.getContractFactory("ArbitrageFactory");
    const factory = await ArbitrageFactory.deploy({
      gasPrice,
      gasLimit: 12000000 // Increased gas limit
    });

    console.log("Waiting for ArbitrageFactory deployment...");
    await factory.deployed();
    console.log("ArbitrageFactory deployed to:", factory.address);

    // Get configuration from environment
    const aaveAddressProvider = "0x012bAC54348C0E635dCAc9D5FB99f06F24136C9A"; // Sepolia Aave address
    const defaultMinProfitBasisPoints = parseInt(process.env.DEFAULT_MIN_PROFIT_BASIS_POINTS);
    const defaultMaxTradeSize = process.env.DEFAULT_MAX_TRADE_SIZE;
    const emergencyWithdrawalDelay = parseInt(process.env.EMERGENCY_WITHDRAWAL_DELAY);

    console.log("\nDeploying components with parameters:");
    console.log("Aave Address Provider:", aaveAddressProvider);
    console.log("Min Profit Basis Points:", defaultMinProfitBasisPoints);
    console.log("Max Trade Size:", hre.ethers.utils.formatEther(defaultMaxTradeSize), "ETH");
    console.log("Emergency Withdrawal Delay:", emergencyWithdrawalDelay, "seconds");

    // Deploy components with dynamic gas settings
    console.log("\nDeploying components...");
    const tx = await factory.deployComponents(
      aaveAddressProvider,
      defaultMinProfitBasisPoints,
      defaultMaxTradeSize,
      emergencyWithdrawalDelay,
      {
        gasPrice,
        gasLimit: 12000000
      }
    );

    console.log("Transaction hash:", tx.hash);
    console.log("Waiting for confirmation...");

    const receipt = await tx.wait();
    console.log("Transaction confirmed in block:", receipt.blockNumber);

    // Get deployed component addresses
    const components = await factory.getComponents();
    console.log("\nDeployed Components:");
    for (let i = 0; i < components.addresses.length; i++) {
      console.log(`${components.names[i]}: ${components.addresses[i]}`);
    }

    // Save deployment info
    const deploymentInfo = {
      network: hre.network.name,
      factory: factory.address,
      deploymentBlock: receipt.blockNumber,
      timestamp: new Date().toISOString(),
      components: Object.fromEntries(components.names.map((name, i) => [name, components.addresses[i]])),
      parameters: {
        aaveAddressProvider,
        defaultMinProfitBasisPoints,
        defaultMaxTradeSize: defaultMaxTradeSize.toString(),
        emergencyWithdrawalDelay
      }
    };

    fs.writeFileSync(
      path.join(__dirname, "../deployments/arbitrage_system.json"),
      JSON.stringify(deploymentInfo, null, 2)
    );

    console.log("\nDeployment addresses saved to deployments/arbitrage_system.json");

    // Verify contracts if ETHERSCAN_API_KEY is available
    if (process.env.ETHERSCAN_API_KEY) {
      console.log("\nVerifying contracts on Etherscan...");
      await hre.run("verify:verify", {
        address: factory.address,
        constructorArguments: []
      });
      console.log("Verification complete");
    }

  } catch (error) {
    console.error("\nDeployment failed:");
    console.error("Error message:", error.message);
    if (error.receipt) {
      console.error("Transaction receipt:", error.receipt);
    }
    throw error;
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
