const { ethers } = require("hardhat");

const WETH_ADDRESS = "0xe39Ab88f8A4777030A534146A9Ca3B52bd5D43A3";
const WETH_ABI = [
  "function deposit() external payable",
  "function withdraw(uint256) external",
  "function balanceOf(address) external view returns (uint256)"
];

async function main() {
  const [signer] = await ethers.getSigners();
  console.log("Using account:", signer.address);

  const weth = new ethers.Contract(WETH_ADDRESS, WETH_ABI, signer);

  // Amount to wrap (0.1 ETH)
  const wrapAmount = ethers.utils.parseEther("0.1");

  console.log(`Wrapping ${ethers.utils.formatEther(wrapAmount)} ETH to WETH...`);

  try {
    const tx = await weth.deposit({ value: wrapAmount });
    await tx.wait();
    console.log("Successfully wrapped ETH to WETH");

    const balance = await weth.balanceOf(signer.address);
    console.log(`New WETH balance: ${ethers.utils.formatEther(balance)} WETH`);
  } catch (error) {
    console.error("Error wrapping ETH:", error);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
