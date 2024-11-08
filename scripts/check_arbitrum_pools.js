const { ethers } = require("hardhat");

const FACTORY_ADDRESS = "0x4893376342d5D7b3e31d4184c08b265e5aB2A3f6";
const WETH_ADDRESS = "0xe39Ab88f8A4777030A534146A9Ca3B52bd5D43A3";
const USDC_ADDRESS = "0x8FB1E3fC51F3b789dED7557E680551d93Ea9d892";

const FACTORY_ABI = [
  "function getPool(address tokenA, address tokenB, uint24 fee) external view returns (address pool)",
  "function feeAmountTickSpacing(uint24) external view returns (int24)"
];

const POOL_ABI = [
  "function token0() external view returns (address)",
  "function token1() external view returns (address)",
  "function fee() external view returns (uint24)",
  "function liquidity() external view returns (uint128)",
  "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)"
];

async function main() {
  const [signer] = await ethers.getSigners();
  console.log("Using account:", signer.address);

  const factory = new ethers.Contract(FACTORY_ADDRESS, FACTORY_ABI, signer);

  // Check common fee tiers
  const feeTiers = [500, 3000, 10000];

  for (const fee of feeTiers) {
    console.log(`\nChecking WETH/USDC pool with ${fee/10000}% fee:`);

    try {
      const poolAddress = await factory.getPool(WETH_ADDRESS, USDC_ADDRESS, fee);

      if (poolAddress === ethers.constants.AddressZero) {
        console.log(`No pool exists for ${fee/10000}% fee tier`);
        continue;
      }

      const pool = new ethers.Contract(poolAddress, POOL_ABI, signer);
      console.log("Pool address:", poolAddress);

      const [token0, token1, poolFee, liquidity, slot0] = await Promise.all([
        pool.token0(),
        pool.token1(),
        pool.fee(),
        pool.liquidity(),
        pool.slot0()
      ]);

      console.log("Token0:", token0);
      console.log("Token1:", token1);
      console.log("Fee:", poolFee);
      console.log("Liquidity:", liquidity.toString());
      console.log("Current tick:", slot0.tick);

      const price = parseFloat(slot0.sqrtPriceX96) ** 2 / (2 ** 192);
      console.log("Price:", price);
    } catch (error) {
      console.error(`Error checking ${fee/10000}% pool:`, error);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
