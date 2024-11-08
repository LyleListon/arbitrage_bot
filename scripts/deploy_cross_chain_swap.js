const hre = require("hardhat");

async function main() {
  console.log("Deploying CrossChainAtomicSwap to Sepolia...");

  // Get the contract factory
  const CrossChainAtomicSwap = await hre.ethers.getContractFactory("CrossChainAtomicSwap");

  // Deploy the contract
  // Replace 'BRIDGE_ADDRESS' with the actual bridge address or a placeholder address for now
  const bridgeAddress = "0x0000000000000000000000000000000000000000"; // Placeholder address
  const crossChainAtomicSwap = await CrossChainAtomicSwap.deploy(bridgeAddress);

  // Wait for the contract to be deployed
  await crossChainAtomicSwap.deployed();

  console.log("CrossChainAtomicSwap deployed to:", crossChainAtomicSwap.address);

  // Verify the contract on Etherscan
  console.log("Verifying contract on Etherscan...");

  await hre.run("verify:verify", {
    address: crossChainAtomicSwap.address,
    constructorArguments: [bridgeAddress],
  });

  console.log("Deployment and verification complete!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
