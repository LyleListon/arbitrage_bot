<<<<<<< HEAD
"""Enhanced Price Monitor Script with Advanced Arbitrage Detection"""

import time
import logging
from typing import Dict, List, Tuple
from decimal import Decimal
from web3 import Web3
from dashboard.price_analysis import PriceAnalyzer
from dashboard.advanced_trading import AdvancedTradingStrategy
from dashboard.advanced_arbitrage_detector import AdvancedArbitrageDetector

def format_opportunity(opp: Dict) -> str:
    """Format opportunity data in a clear, structured way"""
    output = []
    
    # Header based on opportunity type
    if opp.get('type') == 'cross_dex':
        output.extend([
            f"Cross-DEX Opportunity:",
            f"  Buy DEX: {opp['buy_dex']}",
            f"  Sell DEX: {opp['sell_dex']}",
            f"  Token Pair: {opp['token_pair']}",
            f"  Spread: {opp['spread']:.2f}%",
            f"  Est. Profit: ${opp['estimated_profit']:.2f}",
        ])
    elif opp.get('type') == 'multi_hop':
        output.extend([
            f"Multi-Hop Opportunity:",
            f"  Path: {' → '.join(opp['path'])}",
            f"  Steps: {opp['steps']}",
            f"  Est. Profit: ${opp['estimated_profit']:.2f}",
        ])
    else:
        output.extend([
            f"Flash Loan Opportunity:",
            f"  Token In: {opp['token_in']}",
            f"  Token Out: {opp['token_out']}",
            f"  Amount: {opp['flash_loan_amount']} {opp['token_in']}",
            f"  Est. Profit: ${opp['expected_profit']:.2f}",
            f"  ROI: {opp['profit_percentage']:.2f}%",
        ])
    
    # Common fields
    output.extend([
        f"  Confidence Score: {opp['confidence_score']:.2f}",
        f"  Flash Loan Fee: ${float(opp.get('flash_loan_fee', 0)) * 3600:.2f}",  # Convert ETH to USD
    ])
    
    return "\n".join(output)

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Initialize components
    price_analyzer = PriceAnalyzer(history_window=3600)
    trading_strategy = AdvancedTradingStrategy()
    arbitrage_detector = AdvancedArbitrageDetector()
    
    # Token pairs and fee tiers to monitor (expanded list)
    pairs: List[Tuple[str, str, str]] = [
        # ETH Pairs
        ('ETH', 'USDC', '0.05%'),
        ('WETH', 'USDC', '0.05%'),
        ('ETH', 'USDT', '0.05%'),
        ('ETH', 'DAI', '0.05%'),
        
        # Stablecoin Pairs
        ('USDC', 'USDT', '0.01%'),
        ('USDC', 'DAI', '0.01%'),
        ('DAI', 'USDT', '0.01%'),
        
        # BTC and ETH Pairs
        ('WBTC', 'USDC', '0.05%'),
        ('WBTC', 'ETH', '0.05%'),
        ('cbETH', 'ETH', '0.05%'),
        
        # DeFi Tokens
        ('UNI', 'USDC', '0.3%'),
        ('AAVE', 'USDC', '0.3%'),
        ('SNX', 'USDC', '0.3%')
    ]
    
    # Flash loan test amounts (optimized for different wallet sizes)
    flash_loan_amounts = {
        'small': [Decimal('1'), Decimal('2'), Decimal('5')],     # $100-500
        'medium': [Decimal('5'), Decimal('10'), Decimal('15')],  # $500-2000
        'large': [Decimal('10'), Decimal('25'), Decimal('50')]   # $2000+
    }
    
    # Print setup information
    logger.info("\n" + "="*50)
    logger.info("Enhanced Base Network Arbitrage Monitor")
    logger.info("="*50)
    
    logger.info("\nWallet Size Tiers:")
    logger.info("1. Small ($100-500)")
    logger.info("   • Focus: Stablecoin pairs")
    logger.info("   • Flash loan sizes: 1-5 ETH")
    logger.info("   • Expected profit: $5-20 per trade")
    
    logger.info("\n2. Medium ($500-2000)")
    logger.info("   • Focus: ETH pairs + Stablecoins")
    logger.info("   • Flash loan sizes: 5-15 ETH")
    logger.info("   • Expected profit: $20-100 per trade")
    
    logger.info("\n3. Large ($2000+)")
    logger.info("   • Focus: All pairs including DeFi")
    logger.info("   • Flash loan sizes: 10-50 ETH")
    logger.info("   • Expected profit: $100+ per trade")
    
    logger.info("\nMonitored Strategies:")
    logger.info("• Flash Loan Arbitrage")
    logger.info("• Cross-DEX Arbitrage")
    logger.info("• Multi-Hop Trading")
    logger.info("• Pattern-Based Trading")
    
    logger.info("\nMonitored Pairs:")
    for category, category_pairs in {
        "ETH Pairs": [p for p in pairs if 'ETH' in p[0] or 'ETH' in p[1]],
        "Stablecoin Pairs": [p for p in pairs if p[0] in ['USDC', 'USDT', 'DAI'] and p[1] in ['USDC', 'USDT', 'DAI']],
        "BTC & ETH Pairs": [p for p in pairs if 'WBTC' in p[0] or 'WBTC' in p[1] or 'cbETH' in p[0]],
        "DeFi Token Pairs": [p for p in pairs if p[0] in ['UNI', 'AAVE', 'SNX'] or p[1] in ['UNI', 'AAVE', 'SNX']]
    }.items():
        logger.info(f"\n{category}:")
        for token_in, token_out, fee_tier in category_pairs:
            logger.info(f"• {token_in}/{token_out} ({fee_tier})")
    
    logger.info("\n" + "="*50)
    
    try:
        while True:
            logger.info("\n" + "="*30 + " Market Update " + "="*30)
            current_prices: Dict[str, Decimal] = {}
            
            # Track opportunities by strategy
            opportunities = {
                "Flash Loan": [],
                "Cross-DEX": [],
                "Multi-Hop": [],
                "Pattern-Based": []
            }
            
            for token_in, token_out, fee_tier in pairs:
                pair_name = f"{token_in}/{token_out}/{fee_tier}"
                
                try:
                    # Get base price and metrics
                    result = price_analyzer.get_token_price(token_in, token_out, fee_tier)
                    if not result:
                        continue
                        
                    price, price_change, price_impacts = result
                    current_prices[pair_name] = price
                    
                    # Get additional metrics
                    volatility = price_analyzer.get_volatility(pair_name) or Decimal('0')
                    volume = price_analyzer.get_volume(pair_name) or Decimal('0')
                    
                    # Print market data
                    logger.info(f"\n📊 {pair_name}")
                    logger.info(f"Price: ${price:,.2f} ({'+' if price_change >= 0 else ''}{price_change:.2f}%)")
                    logger.info(f"Volatility: {volatility:.2f}%")
                    logger.info(f"Volume (5min): ${volume:,.2f}")
                    
                    if volume > Decimal('50'):
                        # 1. Check flash loan opportunities
                        for wallet_size, amounts in flash_loan_amounts.items():
                            for amount in amounts:
                                flash_opp = trading_strategy.analyze_flash_loan_opportunity(
                                    token_in, token_out, amount, price,
                                    Decimal(str(price_impacts[Decimal('1')]/100))
                                )
                                if flash_opp and flash_opp['confidence_score'] > 0.8:
                                    flash_opp['wallet_tier'] = wallet_size
                                    opportunities["Flash Loan"].append(flash_opp)
                        
                        # 2. Check cross-DEX opportunities
                        cross_dex_opps = arbitrage_detector.find_cross_dex_opportunities(f"{token_in}/{token_out}")
                        opportunities["Cross-DEX"].extend(cross_dex_opps)
                        
                        # 3. Check multi-hop opportunities starting with this token
                        multi_hop_opps = arbitrage_detector.find_multi_hop_opportunities(token_in)
                        opportunities["Multi-Hop"].extend(multi_hop_opps)
                        
                        # 4. Analyze historical patterns
                        pattern_analysis = arbitrage_detector.analyze_historical_patterns(pair_name)
                        if pattern_analysis.get('opportunity_score', 0) > 0.7:
                            opportunities["Pattern-Based"].append({
                                'pair': pair_name,
                                'analysis': pattern_analysis
                            })
                
                except Exception as e:
                    logger.error(f"Error processing {pair_name}: {str(e)}")
            
            # Display opportunities by strategy
            logger.info("\n" + "="*30 + " Trading Opportunities " + "="*30)
            
            for strategy, opps in opportunities.items():
                if opps:
                    logger.info(f"\n💰 {strategy} Opportunities:")
                    for opp in opps:
                        logger.info("\n" + "-"*40)
                        logger.info(format_opportunity(opp))
            
            logger.info("\n" + "="*70)
            time.sleep(60)  # Update every minute
            
    except KeyboardInterrupt:
        logger.info("\nStopping monitor...")
    except Exception as e:
        logger.error(f"Error in monitor: {str(e)}")
=======
"""Price monitoring entry point script"""

import os
import sys
import logging
from dotenv import load_dotenv
from dashboard.price_analysis import PriceAnalyzer

def setup_logging() -> None:
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('price_monitor.log')
        ]
    )

def main() -> None:
    """Main entry point"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Ensure RPC URL is set
        if not os.getenv('BASE_RPC_URL'):
            logger.error("BASE_RPC_URL environment variable not set")
            sys.exit(1)
            
        # Initialize and run price monitor
        logger.info("Starting price monitoring...")
        analyzer = PriceAnalyzer()
        analyzer.monitor_prices()
        
    except KeyboardInterrupt:
        logger.info("\nPrice monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error in price monitoring: {str(e)}")
        sys.exit(1)
>>>>>>> 245fdac14b0b9bc65ffd42e3056011a2ab2b4d30

if __name__ == "__main__":
    main()
