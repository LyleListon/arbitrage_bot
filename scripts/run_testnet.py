import os
import sys
import time
from web3 import Web3
from dotenv import load_dotenv
from arbitrage_bot import ArbitrageBot
from logger import setup_logger
from risk_management import RiskManager
from rate_limiter import RateLimiter
from performance_tracker import PerformanceTracker

# Load testnet environment variables
load_dotenv('.env.testnet')

# Set up logging
logger = setup_logger('testnet_bot', 'logs/testnet.log')

def check_prerequisites():
    """Check all prerequisites before starting the bot."""
    required_vars = [
        'TESTNET_ETH_RPC_URL',
        'TESTNET_BSC_RPC_URL',
        'TESTNET_PRIVATE_KEY',
        'TESTNET_BOT_ADDRESS',
        'TESTNET_PRICE_FEED_ADDRESS'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def initialize_web3(network):
    """Initialize Web3 connection with fallback RPC URLs."""
    rpc_url = os.getenv(f'TESTNET_{network.upper()}_RPC_URL')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        raise Exception(f"Failed to connect to {network} testnet")
    
    return w3

def main():
    try:
        logger.info("Starting testnet arbitrage bot...")
        
        # Check prerequisites
        check_prerequisites()
        
        # Initialize connections
        eth_w3 = initialize_web3('ETH')
        bsc_w3 = initialize_web3('BSC')
        
        # Initialize components with conservative testnet settings
        risk_manager = RiskManager(
            max_trade_size=float(os.getenv('MAX_TEST_TRADE_SIZE', '0.1')),
            daily_trade_limit=float(os.getenv('MAX_TEST_TRADE_SIZE', '0.1')) * 5
        )
        
        rate_limiter = RateLimiter(
            max_requests_per_second=2,
            max_requests_per_minute=30
        )
        
        performance_tracker = PerformanceTracker(
            min_profit_threshold=0.005,  # 0.5% for testnet
            max_loss_threshold=0.02,     # 2% for testnet
            monitoring_interval=300       # 5 minutes
        )
        
        # Initialize bot with testnet configuration
        bot = ArbitrageBot()
        
        # Add safety checks
        def safety_checks():
            try:
                # Check balances
                eth_balance = eth_w3.eth.get_balance(bot.wallet_address)
                if eth_w3.from_wei(eth_balance, 'ether') < 0.01:
                    logger.warning("Low ETH balance on testnet")
                    return False
                
                # Check network status
                if not eth_w3.is_connected() or not bsc_w3.is_connected():
                    logger.error("Lost connection to testnet")
                    return False
                
                # Check performance
                if not performance_tracker.check_performance():
                    logger.warning("Performance below threshold")
                    return False
                
                return True
                
            except Exception as e:
                logger.error(f"Safety check failed: {str(e)}")
                return False
        
        # Main loop with safety measures
        logger.info("Bot initialized, starting main loop...")
        
        while True:
            try:
                if not safety_checks():
                    logger.warning("Safety checks failed, pausing for 5 minutes")
                    time.sleep(300)
                    continue
                
                # Rate limiting
                rate_limiter.wait()
                
                # Check for opportunities
                opportunity = bot.find_best_arbitrage_opportunity()
                
                if opportunity:
                    path, profit, dex_sequence = opportunity
                    
                    # Risk management check
                    if risk_manager.can_execute_trade(bot.network, bot.trade_amount):
                        logger.info(f"Executing trade with expected profit: {profit:.2%}")
                        bot.execute_arbitrage(path, profit, dex_sequence)
                    else:
                        logger.warning("Trade blocked by risk management")
                
                # Performance tracking
                performance_tracker.update()
                
                # Cool down
                time.sleep(int(os.getenv('CHECK_INTERVAL', '120')))
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait before retrying
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
