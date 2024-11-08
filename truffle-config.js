/**
 * Arbitrage Bot Truffle Configuration
 * @LAST_POINT: 2024-01-31 - Initial Truffle setup
 */

require('dotenv').config();
const HDWalletProvider = require('@truffle/hdwallet-provider');

// Ensure environment variables are set
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const RPC_URL = process.env.MAINNET_RPC_URL;

if (!PRIVATE_KEY || !RPC_URL) {
  console.error('Please set your PRIVATE_KEY and MAINNET_RPC_URL in a .env file');
  process.exit(1);
}

module.exports = {
  networks: {
    // Development network (default)
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*" // Match any network id
    },

    // Sepolia testnet
    sepolia: {
      provider: () => {
        return new HDWalletProvider({
          privateKeys: [PRIVATE_KEY.startsWith('0x') ? PRIVATE_KEY : `0x${PRIVATE_KEY}`],
          providerOrUrl: RPC_URL,
          addressIndex: 0,
          numberOfAddresses: 1,
          shareNonce: true,
          derivationPath: "m/44'/60'/0'/0/",
          chainId: 11155111
        });
      },
      network_id: 11155111,
      gas: 5500000,
      gasPrice: 25000000000, // 25 gwei
      confirmations: 1,
      timeoutBlocks: 50,
      skipDryRun: true,
      networkCheckTimeout: 10000,
      websockets: false,
      verify: {
        apiUrl: 'https://api-sepolia.etherscan.io',
        apiKey: process.env.ETHERSCAN_API_KEY
      }
    }
  },

  // Configure your compilers
  compilers: {
    solc: {
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
  },

  // Plugin for verification
  plugins: [
    'truffle-plugin-verify'
  ],

  // API keys for contract verification
  api_keys: {
    etherscan: process.env.ETHERSCAN_API_KEY
  },

  // Directory structure
  contracts_directory: "./contracts",
  contracts_build_directory: "./build",
  migrations_directory: "./migrations",
  test_directory: "./test",

  // Mocha configuration for tests
  mocha: {
    timeout: 20000,
    useColors: true,
    reporter: 'spec',
    retries: 2
  }
};
