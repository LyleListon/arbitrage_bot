# Trading Controls for Base Arbitrage Bot
# This module provides real-time trading controls and settings

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
from web3 import Web3

def create_trading_controls():
    """Create trading control panel"""
    st.title("Trading Controls")
    
    # Trading status
    status = st.radio(
        "Trading Status",
        ["Active", "Paused", "Emergency Stop"],
        index=0
    )
    
    if status == "Emergency Stop":
        st.error("⚠️ Trading is currently stopped!")
    elif status == "Paused":
        st.warning("⏸️ Trading is paused")
    else:
        st.success("✅ Trading is active")
    
    # Trading parameters
    st.subheader("Trading Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_profit = st.slider(
            "Minimum Profit (%)",
            min_value=0.1,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="Minimum profit threshold for executing trades"
        )
        
        max_slippage = st.slider(
            "Maximum Slippage (%)",
            min_value=0.1,
            max_value=2.0,
            value=0.5,
            step=0.1,
            help="Maximum allowed slippage per trade"
        )
    
    with col2:
        max_position = st.slider(
            "Maximum Position Size (ETH)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Maximum position size per trade"
        )
        
        max_gas = st.slider(
            "Maximum Gas Price (gwei)",
            min_value=10,
            max_value=200,
            value=50,
            step=5,
            help="Maximum gas price for transactions"
        )
    
    # Token pairs
    st.subheader("Token Pairs")
    
    token_pairs = {
        "ETH/USDC": True,
        "ETH/USDT": True,
        "WBTC/ETH": False,
        "LINK/ETH": False,
        "UNI/ETH": False
    }
    
    for pair, enabled in token_pairs.items():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.checkbox(pair, value=enabled)
        with col2:
            st.write("24h Volume: $1.2M")
        with col3:
            st.write("Spread: 0.15%")
    
    # DEX settings
    st.subheader("DEX Settings")
    
    dex_settings = {
        "BaseSwap": {
            "enabled": True,
            "priority": 1,
            "gas_estimate": 150000
        },
        "UniswapV3": {
            "enabled": True,
            "priority": 2,
            "gas_estimate": 180000
        },
        "SushiSwap": {
            "enabled": False,
            "priority": 3,
            "gas_estimate": 150000
        },
        "Aerodrome": {
            "enabled": False,
            "priority": 4,
            "gas_estimate": 200000
        }
    }
    
    for dex, settings in dex_settings.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.checkbox(dex, value=settings["enabled"])
        with col2:
            st.number_input(f"{dex} Priority", value=settings["priority"], min_value=1, max_value=10)
        with col3:
            st.number_input(f"{dex} Gas", value=settings["gas_estimate"], step=10000)
    
    # Risk controls
    st.subheader("Risk Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input(
            "Daily Loss Limit ($)",
            value=1000,
            min_value=100,
            help="Maximum allowed daily loss"
        )
        
        st.number_input(
            "Max Open Positions",
            value=3,
            min_value=1,
            help="Maximum number of concurrent positions"
        )
    
    with col2:
        st.number_input(
            "Position Timeout (sec)",
            value=60,
            min_value=10,
            help="Maximum time to hold a position"
        )
        
        st.number_input(
            "Cooldown Period (sec)",
            value=30,
            min_value=5,
            help="Wait time between trades"
        )
    
    # Emergency controls
    st.subheader("Emergency Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🛑 Emergency Stop", help="Immediately stop all trading"):
            st.error("Trading stopped!")
            
        if st.button("💰 Emergency Withdraw", help="Withdraw all funds to safe address"):
            st.warning("Initiating emergency withdrawal...")
    
    with col2:
        if st.button("🔄 Reset Risk Limits", help="Reset all risk limits to defaults"):
            st.info("Risk limits reset to defaults")
            
        if st.button("🔒 Lock Settings", help="Lock all settings"):
            st.success("Settings locked")
    
    # Save changes
    if st.button("Save Changes", help="Save all trading control settings"):
        st.success("Settings saved successfully!")
        
        # Log changes
        st.write("Changes saved at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.write("New settings:")
        st.json({
            "trading_status": status,
            "min_profit": min_profit,
            "max_slippage": max_slippage,
            "max_position": max_position,
            "max_gas": max_gas
        })
