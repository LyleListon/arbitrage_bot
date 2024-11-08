require("@nomiclabs/hardhat-ethers");
require("@nomiclabs/hardhat-waffle");
require("@nomicfoundation/hardhat-verify");
require("dotenv").config();

// Validate required environment variables
const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY;
const MAX_GAS_PRICE_GWEI = process.env.MAX_GAS_PRICE_GWEI || "50";

if (!SEPOLIA_RPC_URL || !PRIVATE_KEY) {
  throw new Error("Missing required environment variables");
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    compilers: [
      {
        version: "0.8.19",
        settings: {
          optimizer: {
            enabled: true,
            runs: 200
          },
          viaIR: true,
          evmVersion: "london"
        }
      }
    ]
  },
  networks: {
    hardhat: {
      chainId: 31337,
      forking: {
        url: SEPOLIA_RPC_URL,
        blockNumber: 6992273
      }
    },
    sepolia: {
      url: SEPOLIA_RPC_URL,
      accounts: [PRIVATE_KEY],
      chainId: 11155111,
      blockConfirmations: 2,
      gasPrice: parseInt(MAX_GAS_PRICE_GWEI) * 1000000000, // Convert gwei to wei
      gas: 12000000 // Increased gas limit for complex deployments
    },
    goerli: {
      url: process.env.GOERLI_RPC_URL || "https://goerli.infura.io/v3/${process.env.INFURA_API_KEY}",
      accounts: [PRIVATE_KEY],
      chainId: 5,
      blockConfirmations: 2,
      gasPrice: parseInt(MAX_GAS_PRICE_GWEI) * 1000000000,
      gas: 12000000
    },
    arbitrum: {
      url: process.env.ARBITRUM_RPC_URL || "https://arb1.arbitrum.io/rpc",
      accounts: [PRIVATE_KEY],
      chainId: 42161,
      blockConfirmations: 1, // Faster finality on L2
      gas: 'auto',
      gasPrice: 'auto',
      // Arbitrum specific settings
      verify: {
        etherscan: {
          apiUrl: "https://api.arbiscan.io",
          apiKey: process.env.ARBISCAN_API_KEY
        }
      }
    },
    arbitrumGoerli: {
      url: process.env.ARBITRUM_GOERLI_RPC_URL || "https://goerli-rollup.arbitrum.io/rpc",
      accounts: [PRIVATE_KEY],
      chainId: 421613,
      blockConfirmations: 1,
      gas: 'auto',
      gasPrice: 'auto'
    }
  },
  etherscan: {
    apiKey: ETHERSCAN_API_KEY
  },
  sourcify: {
    enabled: true
  },
  mocha: {
    timeout: 200000 // Increased timeout for complex deployments
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
