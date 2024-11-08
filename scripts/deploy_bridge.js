const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

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
    await ensureDeploymentDir();

    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying bridge contracts with account:", deployer.address);

    const balance = await deployer.getBalance();
    console.log("Account balance:", hre.ethers.utils.formatEther(balance), "ETH");

    // Get current gas price
    const gasPrice = await getGasPrice();
    console.log("Current gas price:", hre.ethers.utils.formatUnits(gasPrice, "gwei"), "gwei");

    // Deploy CrossChainBridge
    console.log("\nDeploying CrossChainBridge...");
    const minConfirmationBlocks = 5; // Configurable based on chain

    const CrossChainBridge = await hre.ethers.getContractFactory("CrossChainBridge");
    const bridge = await CrossChainBridge.deploy(
      minConfirmationBlocks,
      {
        gasPrice,
        gasLimit: 5000000
      }
    );

    console.log("Waiting for CrossChainBridge deployment...");
    await bridge.deployed();
    console.log("CrossChainBridge deployed to:", bridge.address);

    // Configure supported chains
    console.log("\nConfiguring supported chains...");

    // Sepolia configuration
    const sepoliaConfig = {
      chainId: 11155111,
      confirmations: 5,
      gasLimit: 3000000
    };

    // Get the swap contract address from arbitrage_system.json
    let swapAddress;
    try {
      const deploymentInfo = JSON.parse(
        fs.readFileSync(path.join(__dirname, "../deployments/arbitrage_system.json"))
      );
      swapAddress = deploymentInfo.components.arbitrageBot;
      console.log("Found swap contract address:", swapAddress);
    } catch (error) {
      console.warn("Warning: Could not find arbitrage_system.json. Using zero address for now.");
      swapAddress = "0x0000000000000000000000000000000000000000";
    }

    // Configure Sepolia
    console.log("\nConfiguring Sepolia...");
    const configureTx = await bridge.configureChain(
      sepoliaConfig.chainId,
      sepoliaConfig.confirmations,
      sepoliaConfig.gasLimit,
      swapAddress,
      {
        gasPrice,
        gasLimit: 2000000
      }
    );

    console.log("Waiting for chain configuration...");
    const receipt = await configureTx.wait();
    console.log("Sepolia configured successfully in block:", receipt.blockNumber);

    // Save deployment info
    const deploymentInfo = {
      network: hre.network.name,
      bridge: {
        address: bridge.address,
        deploymentBlock: receipt.blockNumber,
        timestamp: new Date().toISOString(),
        config: {
          minConfirmationBlocks,
          supportedChains: {
            sepolia: {
              chainId: sepoliaConfig.chainId,
              confirmations: sepoliaConfig.confirmations,
              gasLimit: sepoliaConfig.gasLimit,
              swapAddress
            }
          }
        }
      }
    };

    fs.writeFileSync(
      path.join(__dirname, "../deployments/bridge_deployment.json"),
      JSON.stringify(deploymentInfo, null, 2)
    );

    console.log("\nDeployment addresses saved to deployments/bridge_deployment.json");

    // Try to verify the contract
    if (process.env.ETHERSCAN_API_KEY) {
      console.log("\nWaiting for 5 block confirmations before verification...");
      await bridge.deployTransaction.wait(5);

      console.log("Attempting contract verification...");
      try {
        await hre.run("verify:verify", {
          address: bridge.address,
          constructorArguments: [minConfirmationBlocks]
        });
        console.log("Contract verified successfully");
      } catch (error) {
        if (error.message.includes("Already Verified")) {
          console.log("Contract was already verified");
        } else {
          console.warn("Verification failed:", error.message);
          console.log("Contract can be verified manually with:");
          console.log(`npx hardhat verify --network ${hre.network.name} ${bridge.address} ${minConfirmationBlocks}`);
        }
      }
    } else {
      console.log("\nSkipping contract verification - ETHERSCAN_API_KEY not found");
      console.log("To verify manually, run:");
      console.log(`npx hardhat verify --network ${hre.network.name} ${bridge.address} ${minConfirmationBlocks}`);
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
