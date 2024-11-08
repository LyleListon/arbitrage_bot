"""
Price Feed Verification Script
Tests direct interaction with Chainlink price feeds on Sepolia
"""

from web3 import Web3
import json
import os
from dotenv import load_dotenv
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_abi():
    """Load Chainlink price feed ABI"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        abi_path = os.path.join(script_dir, 'chainlink_abi.json')
        with open(abi_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading ABI: {str(e)}")
        return None


def verify_price_feed(w3, address, feed_name):
    """Verify price feed contract at address"""
    try:
        # Load ABI
        abi = load_abi()
        if not abi:
            return False

        # Create contract instance
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi
        )

        # Try to get decimals
        decimals = contract.functions.decimals().call()
        logger.info(f"{feed_name} Decimals: {decimals}")

        # Try to get latest round data
        round_data = contract.functions.latestRoundData().call()
        price = round_data[1] / (10 ** decimals)
        timestamp = round_data[3]
        
        logger.info(f"{feed_name} Price: ${price:.2f}")
        logger.info(f"{feed_name} Timestamp: {timestamp}")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying {feed_name}: {str(e)}")
        return False


def main():
    """Main verification function"""
    try:
        # Load environment variables from root directory
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env.sepolia')
        load_dotenv(env_path)
        
        # Try both RPC endpoints
        rpc_urls = [
            os.getenv('SEPOLIA_RPC_URL'),
            'https://rpc.sepolia.org'
        ]
        
        # Price feed addresses from deploy_config.json
        price_feeds = {
            'ETH/USD': '0x694AA1769357215DE4FAC081bf1f309aDC325306',
            'USDC/USD': '0xA2F78ab2355fe2f984D808B5CeE7FD0A93D5270E',
            'BTC/USD': '0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43',
            'DAI/USD': '0x14866185B1962B63C3Ea9E03Bc1da838bab34C19',
            'LINK/USD': '0xc59E3633BAAC79493d908e63626716e204A45EdF'
        }
        
        for rpc_url in rpc_urls:
            logger.info("Testing with Sepolia RPC URL")
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not w3.is_connected():
                logger.error(f"Failed to connect to {rpc_url}")
                continue
                
            logger.info(f"Connected to network: {w3.eth.chain_id}")
            
            # Verify all price feeds
            success = True
            for feed_name, address in price_feeds.items():
                logger.info(f"\nVerifying {feed_name} feed...")
                if not verify_price_feed(w3, address, feed_name):
                    success = False
            
            if success:
                logger.info("\nAll price feeds verified successfully!")
                break
            else:
                logger.warning("Some price feeds failed verification")
                
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")


if __name__ == '__main__':
    main()
