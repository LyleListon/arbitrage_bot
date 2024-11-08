const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PriceFeedRegistry", function() {
  let priceFeedRegistry;
  let owner;
  let addr1;

  // Sepolia addresses
  const CHAINLINK_ETH_USD_FEED = "0x694AA1769357215DE4FAC081bf1f309aDC325306";
  const SEPOLIA_ETH = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9";
  const SEPOLIA_USDC = "0xda9d4f9b69ac6C22e444eD9aF0CfC043b7a7f53f";

  beforeEach(async function() {
    [owner, addr1] = await ethers.getSigners();

    const PriceFeedRegistry = await ethers.getContractFactory("PriceFeedRegistry");
    priceFeedRegistry = await PriceFeedRegistry.deploy();
    await priceFeedRegistry.deployed();
  });

  describe("Initialization", function() {
    it("Should set the right owner", async function() {
      expect(await priceFeedRegistry.owner()).to.equal(owner.address);
    });

    it("Should not have ETH/USD feed registered initially", async function() {
      expect(await priceFeedRegistry.hasPriceFeed(SEPOLIA_ETH, SEPOLIA_USDC)).to.equal(false);
    });
  });

  describe("Price Feed Registration", function() {
    it("Should register ETH/USD price feed", async function() {
      await priceFeedRegistry.registerPriceFeed(
        SEPOLIA_ETH,
        SEPOLIA_USDC,
        CHAINLINK_ETH_USD_FEED,
        3600 // 1 hour stale threshold
      );

      expect(await priceFeedRegistry.hasPriceFeed(SEPOLIA_ETH, SEPOLIA_USDC)).to.equal(true);
      expect(await priceFeedRegistry.getPriceFeed(SEPOLIA_ETH, SEPOLIA_USDC))
        .to.equal(CHAINLINK_ETH_USD_FEED);
    });

    it("Should get latest price", async function() {
      await priceFeedRegistry.registerPriceFeed(
        SEPOLIA_ETH,
        SEPOLIA_USDC,
        CHAINLINK_ETH_USD_FEED,
        3600
      );

      const [price, decimals] = await priceFeedRegistry.getPrice(SEPOLIA_ETH, SEPOLIA_USDC);
      expect(price).to.be.gt(0);
      expect(decimals).to.be.gt(0);
    });

    it("Should revert when registering with zero address feed", async function() {
      await expect(
        priceFeedRegistry.registerPriceFeed(
          SEPOLIA_ETH,
          SEPOLIA_USDC,
          ethers.constants.AddressZero,
          3600
        )
      ).to.be.revertedWith("InvalidPriceFeed");
    });

    it("Should revert when registering with zero threshold", async function() {
      await expect(
        priceFeedRegistry.registerPriceFeed(
          SEPOLIA_ETH,
          SEPOLIA_USDC,
          CHAINLINK_ETH_USD_FEED,
          0
        )
      ).to.be.revertedWith("InvalidThreshold");
    });
  });

  describe("Access Control", function() {
    it("Should not allow non-owner to register price feed", async function() {
      await expect(
        priceFeedRegistry.connect(addr1).registerPriceFeed(
          SEPOLIA_ETH,
          SEPOLIA_USDC,
          CHAINLINK_ETH_USD_FEED,
          3600
        )
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });
  });
});
