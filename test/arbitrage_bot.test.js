const ArbitrageBot = artifacts.require("ArbitrageBot");
const PriceFeedRegistry = artifacts.require("PriceFeedRegistry");
const DEXRegistry = artifacts.require("DEXRegistry");

// Sepolia addresses
const CHAINLINK_ETH_USD_FEED = "0x694AA1769357215DE4FAC081bf1f309aDC325306";
const UNISWAP_V2_ROUTER = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
const SEPOLIA_ETH = "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9";
const SEPOLIA_USDC = "0xda9d4f9b69ac6C22e444eD9aF0CfC043b7a7f53f";

contract("ArbitrageBot", accounts => {
  let bot, priceFeedRegistry, dexRegistry;
  const owner = accounts[0];

  // Test parameters
  const DEFAULT_MIN_PROFIT_BASIS_POINTS = 100; // 1%
  const DEFAULT_MAX_TRADE_SIZE = web3.utils.toWei("10", "ether");
  const EMERGENCY_WITHDRAWAL_DELAY = 86400; // 24 hours
  const MAX_SLIPPAGE = 100; // 1%
  const GAS_OVERHEAD = 300000; // Estimated gas overhead

  before(async () => {
    // Deploy registries first
    priceFeedRegistry = await PriceFeedRegistry.new({ from: owner });
    dexRegistry = await DEXRegistry.new({ from: owner });

    // Deploy ArbitrageBot with initial parameters
    bot = await ArbitrageBot.new(
      DEFAULT_MIN_PROFIT_BASIS_POINTS,
      DEFAULT_MAX_TRADE_SIZE,
      EMERGENCY_WITHDRAWAL_DELAY,
      { from: owner }
    );

    // Set registries in ArbitrageBot
    await bot.setRegistries(
      priceFeedRegistry.address,
      dexRegistry.address,
      { from: owner }
    );

    // Register ETH/USD price feed
    await priceFeedRegistry.registerPriceFeed(
      SEPOLIA_ETH,
      SEPOLIA_USDC,
      CHAINLINK_ETH_USD_FEED,
      3600, // 1 hour stale threshold
      { from: owner }
    );

    // Register Uniswap V2 DEX
    await dexRegistry.registerDEX(
      UNISWAP_V2_ROUTER,
      "Uniswap V2",
      MAX_SLIPPAGE,
      GAS_OVERHEAD,
      { from: owner }
    );

    // Add supported pair
    await dexRegistry.addSupportedPair(
      UNISWAP_V2_ROUTER,
      SEPOLIA_ETH,
      SEPOLIA_USDC,
      { from: owner }
    );
  });

  describe("Initialization", () => {
    it("should have correct initial parameters", async () => {
      const minProfit = await bot.defaultMinProfitBasisPoints();
      const maxTradeSize = await bot.defaultMaxTradeSize();
      const withdrawalDelay = await bot.emergencyWithdrawalDelay();

      assert.equal(minProfit.toString(), DEFAULT_MIN_PROFIT_BASIS_POINTS.toString(), "Incorrect min profit");
      assert.equal(maxTradeSize.toString(), DEFAULT_MAX_TRADE_SIZE.toString(), "Incorrect max trade size");
      assert.equal(withdrawalDelay.toString(), EMERGENCY_WITHDRAWAL_DELAY.toString(), "Incorrect withdrawal delay");
    });

    it("should have correct registry addresses", async () => {
      const registeredPriceFeed = await bot.priceFeedRegistry();
      const registeredDex = await bot.dexRegistry();

      assert.equal(registeredPriceFeed, priceFeedRegistry.address, "Incorrect price feed registry");
      assert.equal(registeredDex, dexRegistry.address, "Incorrect DEX registry");
    });

    it("should have ETH/USD price feed registered", async () => {
      const hasFeed = await priceFeedRegistry.hasPriceFeed(SEPOLIA_ETH, SEPOLIA_USDC);
      assert.equal(hasFeed, true, "ETH/USD price feed not registered");
    });

    it("should have Uniswap V2 registered with ETH/USDC pair", async () => {
      const isPairSupported = await dexRegistry.isPairSupported(
        UNISWAP_V2_ROUTER,
        SEPOLIA_ETH,
        SEPOLIA_USDC
      );
      assert.equal(isPairSupported, true, "ETH/USDC pair not supported on Uniswap V2");
    });
  });

  describe("Emergency Controls", () => {
    it("should handle emergency withdrawal request correctly", async () => {
      await bot.requestEmergencyWithdrawal({ from: owner });

      const requested = await bot.emergencyWithdrawalRequested();
      assert.equal(requested, true, "Emergency withdrawal not requested");

      await bot.cancelEmergencyWithdrawal({ from: owner });
      const cancelled = await bot.emergencyWithdrawalRequested();
      assert.equal(cancelled, false, "Emergency withdrawal not cancelled");
    });

    it("should pause and unpause correctly", async () => {
      await bot.pause({ from: owner });
      const paused = await bot.paused();
      assert.equal(paused, true, "Contract not paused");

      await bot.unpause({ from: owner });
      const unpaused = await bot.paused();
      assert.equal(unpaused, false, "Contract not unpaused");
    });
  });
});
