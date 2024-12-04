VVB                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb break                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffq
import os

# Add more detailed import error handling
def check_and_import_libraries():
    """
    Check and import required libraries with detailed error handling
    
    Returns:
        Tuple of imported libraries or raises ImportError
    """
    try:
        import streamlit as st
        import pandas as pd
        import plotly.express as px
        return st, pd, px
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please install required libraries:")
        print("pip install streamlit pandas plotly")
        sys.exit(1)

# Perform library import
st, pd, px = check_and_import_libraries()

import logging
import json
from datetime import datetime

# Configure logging with more detailed output
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more information
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path=None):
    """
    Load configuration with robust error handling
    
    Args:
        config_path (str, optional): Path to config file
    
    Returns:
        Dict containing configuration
    """
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        return {}

def save_config(config, config_path=None):
    """
    Save configuration to file
    
    Args:
        config (dict): Configuration to save
        config_path (str, optional): Path to save config file
    """
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Configuration saved to {config_path}")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        st.error(f"Could not save configuration: {e}")

def get_dex_resources():
    """
    Provide resources for obtaining DEX connection information
    
    Returns:
        List of dictionaries with DEX resources
    """
    return [
        {
            "name": "Uniswap",
            "api_docs": "https://docs.uniswap.org/protocol/reference/API",
            "endpoint": "https://api.uniswap.org/v2",
            "notes": "Requires GraphQL API access"
        },
        {
            "name": "SushiSwap",
            "api_docs": "https://dev.sushi.com/docs/Developers/Integrations/API",
            "endpoint": "https://api.sushi.com/v1",
            "notes": "Provides liquidity and swap information"
        },
        {
            "name": "PancakeSwap",
            "api_docs": "https://docs.pancakeswap.finance/developers/api",
            "endpoint": "https://api.pancakeswap.com/v1",
            "notes": "Primarily for Binance Smart Chain"
        }
    ]

def main():
    """Main Streamlit dashboard function"""
    st.set_page_config(page_title="Arbitrage Bot DEX Connections", page_icon="🔗", layout="wide")
    
    st.title("Decentralized Exchange (DEX) Connection Guide")
    
    # DEX Resources Section
    st.header("DEX Connection Resources")
    
    dex_resources = get_dex_resources()
    
    for dex in dex_resources:
        with st.expander(f"{dex['name']} DEX Connection"):
            st.write(f"**API Documentation**: [{dex['name']} API Docs]({dex['api_docs']})")
            st.write(f"**Endpoint**: `{dex['endpoint']}`")
            st.write(f"**Notes**: {dex['notes']}")
            
            st.subheader("Connection Steps")
            st.code(f"""
1. Visit {dex['name']} API documentation
2. Create an account/API key
3. Obtain API endpoint and credentials
4. Add to config.json:
{{
    "dex_connections": [
        {{
            "name": "{dex['name']}",
            "endpoint": "{dex['endpoint']}",
            "api_key": "YOUR_API_KEY"
        }}
    ]
}}
            """)
    
    # Additional Resources Section
    st.header("Additional Resources")
    
    st.markdown("""
    ### Finding DEX Connection Information
    - **API Documentation**: Always refer to the official API docs
    - **Developer Communities**: 
      * Discord channels
      * Telegram groups
      * GitHub repositories
    - **Web3 Development Resources**:
      * CoinGecko API
      * 1inch API
      * Moralis Web3 API
    
    ### Recommended Approach
    1. Research multiple DEXes
    2. Compare API capabilities
    3. Check rate limits and pricing
    4. Ensure compatibility with your arbitrage strategy
    """)
    
    # Configuration Reminder
    st.info("""
    💡 Tip: When adding DEX connections, ensure you:
    - Have necessary API credentials
    - Understand rate limits
    - Comply with terms of service
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Dashboard initialization error: {e}", exc_info=True)
        st.error(f"Error initializing dashboard: {e}")
