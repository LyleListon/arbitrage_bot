"""
API Testing Script
Tests all dashboard API endpoints and verifies response formats
"""

import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:5000"

def test_stats():
    """Test /api/stats endpoint"""
    logger.info("Testing /api/stats...")
    response = requests.get(f"{BASE_URL}/api/stats")
    data = response.json()
    logger.info(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def test_wallet_balance():
    """Test /api/wallet_balance endpoint"""
    logger.info("Testing /api/wallet_balance...")
    response = requests.get(f"{BASE_URL}/api/wallet_balance")
    data = response.json()
    logger.info(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def test_trades():
    """Test /api/trades endpoint"""
    logger.info("Testing /api/trades...")
    response = requests.get(f"{BASE_URL}/api/trades")
    data = response.json()
    logger.info(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def test_profit_history():
    """Test /api/profit_history endpoint"""
    logger.info("Testing /api/profit_history...")
    response = requests.get(f"{BASE_URL}/api/profit_history")
    data = response.json()
    logger.info(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200

def main():
    """Run all API tests"""
    logger.info("Starting API tests...")
    
    tests = [
        test_stats,
        test_wallet_balance,
        test_trades,
        test_profit_history
    ]
    
    results = []
    for test in tests:
        try:
            success = test()
            results.append((test.__name__, success))
        except Exception as e:
            logger.error(f"Error in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))
    
    logger.info("\nTest Results:")
    for name, success in results:
        logger.info(f"{name}: {'✓' if success else '✗'}")

if __name__ == '__main__':
    main()
