const ArbitrageBot = artifacts.require("ArbitrageBot");

contract("ArbitrageBot Basic Tests", accounts => {
  let bot;
  const owner = accounts[0];

  beforeEach(async () => {
    // Deploy a new instance for each test
    bot = await ArbitrageBot.new(
      100, // defaultMinProfitBasisPoints (1%)
      web3.utils.toWei('10', 'ether'), // defaultMaxTradeSize
      86400 // emergencyWithdrawalDelay
    );
  });

  it("should have correct initial parameters", async () => {
    const minProfit = await bot.defaultMinProfitBasisPoints();
    assert.equal(minProfit.toString(), "100", "Incorrect min profit");

    const withdrawalDelay = await bot.emergencyWithdrawalDelay();
    assert.equal(withdrawalDelay.toString(), "86400", "Incorrect withdrawal delay");
  });

  it("should allow owner to configure trading pair", async () => {
    const mockToken1 = "0x1000000000000000000000000000000000000000";
    const mockToken2 = "0x2000000000000000000000000000000000000000";

    await bot.configureTradingPair(
      mockToken1,
      mockToken2,
      200, // 2% min profit
      web3.utils.toWei("5", "ether"), // 5 tokens max trade
      100 // 1% max slippage
    );

    const config = await bot.getPairConfig(mockToken1, mockToken2);
    assert.equal(config.enabled, true, "Pair should be enabled");
  });

  it("should allow owner to authorize tokens", async () => {
    const mockToken = "0x1000000000000000000000000000000000000000";
    
    await bot.setAuthorizedToken(mockToken, true);
    const isAuthorized = await bot.authorizedTokens(mockToken);
    assert.equal(isAuthorized, true, "Token should be authorized");
  });
});
