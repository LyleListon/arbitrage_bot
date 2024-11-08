const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DEXRegistry", function() {
  let dexRegistry;
  let owner;
  let addr1;

  // Sepolia DEX addresses
  const UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
  const SUSHISWAP_ROUTER = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506";

  // Sepolia token addresses
  const SEPOLIA_ETH = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9";
  const SEPOLIA_USDC = "0xda9d4f9b69ac6C22e444eD9aF0CfC043b7a7f53f";

  beforeEach(async function() {
    [owner, addr1] = await ethers.getSigners();

    const DEXRegistry = await ethers.getContractFactory("DEXRegistry");
    dexRegistry = await DEXRegistry.deploy();
    await dexRegistry.deployed();
  });

  describe("DEX Registration", function() {
    it("Should register a DEX correctly", async function() {
      await dexRegistry.registerDEX(
        UNISWAP_V2_ROUTER,
        "Uniswap V2",
        100, // 1% max slippage
        300000 // gas overhead
      );

      const dexInfo = await dexRegistry.getDEXInfo(UNISWAP_V2_ROUTER);
      expect(dexInfo.protocol).to.equal("Uniswap V2");
      expect(dexInfo.maxSlippage).to.equal(100);
      expect(dexInfo.isActive).to.equal(true);
      expect(dexInfo.overhead).to.equal(300000);
    });

    it("Should revert when registering with invalid slippage", async function() {
      await expect(
        dexRegistry.registerDEX(
          UNISWAP_V2_ROUTER,
          "Uniswap V2",
          1001, // > 10% max slippage
          300000
        )
      ).to.be.revertedWith("InvalidSlippage");
    });

    it("Should revert when registering zero address", async function() {
      await expect(
        dexRegistry.registerDEX(
          ethers.constants.AddressZero,
          "Invalid",
          100,
          300000
        )
      ).to.be.revertedWith("InvalidRouter");
    });
  });

  describe("Trading Pair Management", function() {
    beforeEach(async function() {
      await dexRegistry.registerDEX(
        UNISWAP_V2_ROUTER,
        "Uniswap V2",
        100,
        300000
      );
    });

    it("Should add supported trading pair", async function() {
      await dexRegistry.addSupportedPair(
        UNISWAP_V2_ROUTER,
        SEPOLIA_ETH,
        SEPOLIA_USDC
      );

      expect(await dexRegistry.isPairSupported(
        UNISWAP_V2_ROUTER,
        SEPOLIA_ETH,
        SEPOLIA_USDC
      )).to.equal(true);

      // Check reverse direction
      expect(await dexRegistry.isPairSupported(
        UNISWAP_V2_ROUTER,
        SEPOLIA_USDC,
        SEPOLIA_ETH
      )).to.equal(true);
    });

    it("Should remove supported trading pair", async function() {
      await dexRegistry.addSupportedPair(
        UNISWAP_V2_ROUTER,
        SEPOLIA_ETH,
        SEPOLIA_USDC
      );
      await dexRegistry.removeSupportedPair(
        UNISWAP_V2_ROUTER,
        SEPOLIA_ETH,
        SEPOLIA_USDC
      );

      expect(await dexRegistry.isPairSupported(
        UNISWAP_V2_ROUTER,
        SEPOLIA_ETH,
        SEPOLIA_USDC
      )).to.equal(false);
    });
  });

  describe("DEX Management", function() {
    beforeEach(async function() {
      await dexRegistry.registerDEX(
        UNISWAP_V2_ROUTER,
        "Uniswap V2",
        100,
        300000
      );
    });

    it("Should update max slippage", async function() {
      await dexRegistry.updateMaxSlippage(UNISWAP_V2_ROUTER, 200);
      const dexInfo = await dexRegistry.getDEXInfo(UNISWAP_V2_ROUTER);
      expect(dexInfo.maxSlippage).to.equal(200);
    });

    it("Should update gas overhead", async function() {
      await dexRegistry.updateGasOverhead(UNISWAP_V2_ROUTER, 400000);
      const dexInfo = await dexRegistry.getDEXInfo(UNISWAP_V2_ROUTER);
      expect(dexInfo.overhead).to.equal(400000);
    });

    it("Should deactivate and reactivate DEX", async function() {
      await dexRegistry.deactivateDEX(UNISWAP_V2_ROUTER);
      let dexInfo = await dexRegistry.getDEXInfo(UNISWAP_V2_ROUTER);
      expect(dexInfo.isActive).to.equal(false);

      await dexRegistry.reactivateDEX(UNISWAP_V2_ROUTER);
      dexInfo = await dexRegistry.getDEXInfo(UNISWAP_V2_ROUTER);
      expect(dexInfo.isActive).to.equal(true);
    });
  });

  describe("Trade Validation", function() {
    beforeEach(async function() {
      await dexRegistry.registerDEX(
        UNISWAP_V2_ROUTER,
        "Uniswap V2",
        100,
        300000
      );
      await dexRegistry.addSupportedPair(
        UNISWAP_V2_ROUTER,
        SEPOLIA_ETH,
        SEPOLIA_USDC
      );
    });

    it("Should validate supported trading pair", async function() {
      await expect(
        dexRegistry.validateTrade(
          UNISWAP_V2_ROUTER,
          SEPOLIA_ETH,
          SEPOLIA_USDC
        )
      ).to.not.be.reverted;
    });

    it("Should revert on unsupported trading pair", async function() {
      await expect(
        dexRegistry.validateTrade(
          UNISWAP_V2_ROUTER,
          SEPOLIA_ETH,
          SUSHISWAP_ROUTER // Using as dummy token address
        )
      ).to.be.revertedWith("PairNotSupported");
    });

    it("Should revert on inactive DEX", async function() {
      await dexRegistry.deactivateDEX(UNISWAP_V2_ROUTER);
      await expect(
        dexRegistry.validateTrade(
          UNISWAP_V2_ROUTER,
          SEPOLIA_ETH,
          SEPOLIA_USDC
        )
      ).to.be.revertedWith("DEXNotActive");
    });
  });
});
