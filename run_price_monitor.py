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

if __name__ == "__main__":
    main()
