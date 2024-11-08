const PriceFeedRegistry = artifacts.require("PriceFeedRegistry");

contract("PriceFeedRegistry", accounts => {
  let registry;
  const owner = accounts[0];

  // Sepolia addresses
  const CHAINLINK_ETH_USD_FEED = "0x694AA1769357215DE4FAC081bf1f309aDC325306";
  const SEPOLIA_ETH = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9";
  const SEPOLIA_USDC = "0xda9d4f9b69ac6C22e444eD9aF0CfC043b7a7f53f";

  beforeEach(async () => {
    registry = await PriceFeedRegistry.new({ from: owner });
  });

  describe("Initialization", () => {
    it("should be owned by deployer", async () => {
      const actualOwner = await registry.owner();
      assert.equal(actualOwner, owner, "Incorrect owner");
    });

    it("should not have ETH/USD feed registered initially", async () => {
      const hasFeed = await registry.hasPriceFeed(SEPOLIA_ETH, SEPOLIA_USDC);
      assert.equal(hasFeed, false, "Feed should not be registered initially");
    });
  });

  describe("Price Feed Registration", () => {
    it("should register ETH/USD price feed", async () => {
      await registry.registerPriceFeed(
        SEPOLIA_ETH,
        SEPOLIA_USDC,
        CHAINLINK_ETH_USD_FEED,
        3600, // 1 hour stale threshold
        { from: owner }
      );

      const hasFeed = await registry.hasPriceFeed(SEPOLIA_ETH, SEPOLIA_USDC);
      assert.equal(hasFeed, true, "Feed not registered");

      const registeredFeed = await registry.getPriceFeed(SEPOLIA_ETH, SEPOLIA_USDC);
      assert.equal(registeredFeed, CHAINLINK_ETH_USD_FEED, "Incorrect feed address");
    });

    it("should get latest price", async () => {
      await registry.registerPriceFeed(
        SEPOLIA_ETH,
        SEPOLIA_USDC,
        CHAINLINK_ETH_USD_FEED,
        3600,
        { from: owner }
      );

      const [price, decimals] = await registry.getPrice(SEPOLIA_ETH, SEPOLIA_USDC);
      assert(price.gt(web3.utils.toBN(0)), "Price should be greater than 0");
      assert(decimals > 0, "Decimals should be greater than 0");
    });
  });
});
