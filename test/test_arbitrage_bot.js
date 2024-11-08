const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("ArbitrageBot", function () {
  let ArbitrageBot;
  let bot;
  let owner;
  let addr1;
  let addr2;

  beforeEach(async function () {
    // Get signers
    [owner, addr1, addr2] = await ethers.getSigners();

    // Deploy ArbitrageBot
    ArbitrageBot = await ethers.getContractFactory("ArbitrageBot");
    bot = await ArbitrageBot.deploy(
      100, // 1% min profit
      ethers.utils.parseEther("10"), // 10 ETH max trade
      3600 // 1 hour emergency delay
    );
    await bot.deployed();
  });

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      expect(await bot.owner()).to.equal(owner.address);
    });

    it("Should set correct initial parameters", async function () {
      expect(await bot.minProfitBasisPoints()).to.equal(100);
      expect(await bot.maxTradeSize()).to.equal(ethers.utils.parseEther("10"));
      expect(await bot.emergencyWithdrawalDelay()).to.equal(3600);
    });
  });

  describe("Security Features", function () {
    it("Should allow owner to pause/unpause", async function () {
      await bot.pause();
      expect(await bot.paused()).to.equal(true);
      
      await bot.unpause();
      expect(await bot.paused()).to.equal(false);
    });

    it("Should prevent non-owner from pausing", async function () {
      await expect(
        bot.connect(addr1).pause()
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Should handle DEX authorization correctly", async function () {
      const testDex = "0x1234567890123456789012345678901234567890";
      await bot.setAuthorizedDEX(testDex, true);
      expect(await bot.authorizedDEXs(testDex)).to.equal(true);
      
      await bot.setAuthorizedDEX(testDex, false);
      expect(await bot.authorizedDEXs(testDex)).to.equal(false);
    });

    it("Should handle token authorization correctly", async function () {
      const testToken = "0x1234567890123456789012345678901234567890";
      await bot.setAuthorizedToken(testToken, true);
      expect(await bot.authorizedTokens(testToken)).to.equal(true);
      
      await bot.setAuthorizedToken(testToken, false);
      expect(await bot.authorizedTokens(testToken)).to.equal(false);
    });
  });

  describe("Emergency Withdrawal", function () {
    it("Should handle emergency withdrawal request correctly", async function () {
      await bot.requestEmergencyWithdrawal();
      expect(await bot.emergencyWithdrawalRequested()).to.equal(true);
    });

    it("Should prevent immediate withdrawal", async function () {
      await bot.requestEmergencyWithdrawal();
      const tokens = ["0x1234567890123456789012345678901234567890"];
      
      await expect(
        bot.executeEmergencyWithdrawal(tokens)
      ).to.be.revertedWith("Withdrawal delay not elapsed");
    });

    it("Should allow withdrawal after delay", async function () {
      await bot.requestEmergencyWithdrawal();
      
      // Advance time by emergency delay
      await time.increase(3600);
      
      const tokens = ["0x1234567890123456789012345678901234567890"];
      await bot.setAuthorizedToken(tokens[0], true); // Authorize token first
      await expect(
        bot.executeEmergencyWithdrawal(tokens)
      ).not.to.be.reverted;
    });
  });

  describe("Parameter Updates", function () {
    it("Should allow owner to update parameters", async function () {
      const newMinProfit = 200;
      const newMaxTrade = ethers.utils.parseEther("20");
      const newDelay = 7200;
      
      await bot.updateParameters(newMinProfit, newMaxTrade, newDelay);
      
      expect(await bot.minProfitBasisPoints()).to.equal(newMinProfit);
      expect(await bot.maxTradeSize()).to.equal(newMaxTrade);
      expect(await bot.emergencyWithdrawalDelay()).to.equal(newDelay);
    });

    it("Should prevent non-owner from updating parameters", async function () {
      await expect(
        bot.connect(addr1).updateParameters(200, ethers.utils.parseEther("20"), 7200)
      ).to.be.revertedWith("Ownable: caller is not the owner");
    });

    it("Should validate parameter values", async function () {
      await expect(
        bot.updateParameters(0, ethers.utils.parseEther("20"), 7200)
      ).to.be.revertedWith("Min profit must be > 0");
      
      await expect(
        bot.updateParameters(200, 0, 7200)
      ).to.be.revertedWith("Max trade size must be > 0");
      
      await expect(
        bot.updateParameters(200, ethers.utils.parseEther("20"), 0)
      ).to.be.revertedWith("Emergency withdrawal delay must be > 0");
    });
  });
});
