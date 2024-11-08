# Advanced Dashboard for Base Arbitrage Bot
# This module provides comprehensive monitoring and control features:
# 1. Real-time analytics
# 2. Performance tracking
# 3. Risk management
# 4. ML insights

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import sys
import json
from web3 import Web3
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.append('..')
from scripts.ml_predictor import MLPredictor
from scripts.opportunity_predictor import OpportunityPredictor
from scripts.monitor_advanced import monitor_advanced
from scripts.risk_management import RiskManager

# Load configuration
with open('../config.json', 'r') as f:
    config = json.load(f)

# Initialize components
ml_predictor = MLPredictor()
opportunity_predictor = OpportunityPredictor()
risk_manager = RiskManager()

# Configure Streamlit page
st.set_page_config(
    page_title="Base Arbitrage Advanced Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117
    }
    .sidebar .sidebar-content {
        background: #262730
    }
    .Widget>label {
        color: #ffffff
    }
    .stProgress .st-bo {
        background-color: #21c354
    }
</style>
""", unsafe_allow_html=True)

def create_3d_surface_plot(data: pd.DataFrame) -> go.Figure:
    """Create 3D surface plot of price relationships"""
    fig = go.Figure(data=[go.Surface(z=data.values)])
    fig.update_layout(
        title='Price Surface Analysis',
        scene = dict(
            xaxis_title='Time',
            yaxis_title='DEX',
            zaxis_title='Price'
        ),
        autosize=False,
        width=800,
        height=600,
        margin=dict(l=65, r=50, b=65, t=90)
    )
    return fig

def create_network_graph(correlations: pd.DataFrame) -> go.Figure:
    """Create network graph of DEX relationships"""
    fig = go.Figure()
    
    # Create nodes for each DEX
    for i, dex in enumerate(correlations.index):
        fig.add_trace(go.Scatter(
            x=[i],
            y=[0],
            mode='markers+text',
            name=dex,
            text=[dex],
            marker=dict(size=20),
            textposition="bottom center"
        ))
    
    # Add edges between nodes
    for i in range(len(correlations.index)):
        for j in range(i+1, len(correlations.index)):
            correlation = correlations.iloc[i,j]
            width = abs(correlation) * 5
            color = 'red' if correlation < 0 else 'green'
            
            fig.add_trace(go.Scatter(
                x=[i, j],
                y=[0, 0],
                mode='lines',
                line=dict(width=width, color=color),
                showlegend=False
            ))
    
    fig.update_layout(
        title='DEX Correlation Network',
        showlegend=True,
        hovermode='closest'
    )
    
    return fig

def create_risk_heatmap(risk_data: pd.DataFrame) -> go.Figure:
    """Create risk heatmap"""
    fig = px.imshow(
        risk_data,
        labels=dict(color="Risk Score"),
        color_continuous_scale='RdYlGn_r',
        aspect='auto'
    )
    
    fig.update_layout(
        title='Risk Analysis Heatmap',
        xaxis_title='Risk Factors',
        yaxis_title='Token Pairs'
    )
    
    return fig

def create_performance_dashboard():
    """Create performance metrics dashboard"""
    st.subheader("Performance Metrics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Profit",
            "$1,234.56",
            "+5.6%",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Success Rate",
            "87%",
            "+2.3%",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Average ROI",
            "3.2%",
            "-0.5%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Gas Efficiency",
            "92%",
            "+1.8%",
            delta_color="normal"
        )
    
    # Performance chart
    performance_data = pd.DataFrame({
        'date': pd.date_range(start='2024-01-01', end='2024-01-31'),
        'profit': np.random.normal(100, 20, 31).cumsum()
    })
    
    fig = px.line(
        performance_data,
        x='date',
        y='profit',
        title='Cumulative Profit'
    )
    
    st.plotly_chart(fig)

def create_risk_dashboard():
    """Create risk management dashboard"""
    st.subheader("Risk Management")
    
    # Risk settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.slider("Maximum Position Size (ETH)", 0.0, 10.0, 1.0, 0.1)
        st.slider("Minimum Profit Threshold (%)", 0.0, 5.0, 2.0, 0.1)
        
    with col2:
        st.slider("Maximum Gas Price (gwei)", 0, 100, 50, 5)
        st.slider("Maximum Slippage (%)", 0.0, 2.0, 0.5, 0.1)
    
    # Risk metrics
    risk_data = pd.DataFrame(
        np.random.rand(5, 4),
        columns=['Liquidity', 'Volatility', 'Correlation', 'Gas'],
        index=['ETH/USDC', 'ETH/USDT', 'WBTC/ETH', 'LINK/ETH', 'UNI/ETH']
    )
    
    st.plotly_chart(create_risk_heatmap(risk_data))

def create_ml_insights():
    """Create ML insights dashboard"""
    st.subheader("ML Insights")
    
    # Model performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Model Accuracy")
        accuracy_data = pd.DataFrame({
            'model': ['LSTM', 'Random Forest', 'XGBoost'],
            'accuracy': [0.85, 0.82, 0.88]
        })
        
        fig = px.bar(
            accuracy_data,
            x='model',
            y='accuracy',
            title='Model Accuracy Comparison'
        )
        st.plotly_chart(fig)
    
    with col2:
        st.write("Feature Importance")
        importance = ml_predictor.get_feature_importance()
        st.plotly_chart(create_feature_importance_chart(importance))
    
    # Prediction confidence
    st.write("Prediction Confidence Over Time")
    confidence_data = pd.DataFrame({
        'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='H'),
        'confidence': np.random.normal(0.8, 0.1, 100)
    })
    
    fig = px.line(
        confidence_data,
        x='timestamp',
        y='confidence',
        title='Prediction Confidence'
    )
    st.plotly_chart(fig)

def create_system_health():
    """Create system health dashboard"""
    st.subheader("System Health")
    
    # Health metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "API Response Time",
            "45ms",
            "-5ms",
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            "Memory Usage",
            "68%",
            "+2%",
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            "Active Connections",
            "12",
            "+3",
            delta_color="normal"
        )
    
    # System logs
    st.write("System Logs")
    logs = [
        "10:45:23 - Trade executed successfully",
        "10:45:22 - Opportunity detected",
        "10:45:21 - Price update received",
        "10:45:20 - Connection established"
    ]
    
    for log in logs:
        st.text(log)

def main():
    """Main dashboard function"""
    st.title("Base Arbitrage Advanced Dashboard")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Overview", "Performance", "Risk Management", "ML Insights", "System Health"]
    )
    
    # Settings
    st.sidebar.title("Settings")
    token_pair = st.sidebar.selectbox(
        "Select Token Pair",
        [f"{t1}/{t2}" for t1 in config['tokens'] for t2 in config['tokens'] if t1 != t2]
    )
    
    timeframe = st.sidebar.selectbox(
        "Select Timeframe",
        ["1H", "4H", "1D", "1W"]
    )
    
    update_interval = st.sidebar.slider(
        "Update Interval (seconds)",
        min_value=5,
        max_value=60,
        value=10
    )
    
    # Page content
    if page == "Overview":
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Price Analysis")
            token0, token1 = token_pair.split('/')
            prices = opportunity_predictor.price_history[f"{token0}_{token1}"]
            predictions = pd.DataFrame({
                'price_prediction': [
                    ml_predictor.predict_opportunity(
                        prices.iloc[:i],
                        opportunity_predictor.volatility_history[f"{token0}_{token1}"],
                        opportunity_predictor.correlation_history[f"{token0}_{token1}"],
                        opportunity_predictor.market_history[f"{token0}_{token1}"]
                    )['price_prediction']
                    for i in range(len(prices))
                ]
            }, index=prices.index)
            
            st.plotly_chart(create_price_chart(prices, predictions))
            
            st.subheader("DEX Analysis")
            correlations = pd.DataFrame(
                np.random.rand(4, 4),
                index=config['dexes'].keys(),
                columns=config['dexes'].keys()
            )
            st.plotly_chart(create_network_graph(correlations))
        
        with col2:
            st.subheader("Opportunity Analysis")
            opportunities = pd.DataFrame({
                'confidence': [
                    ml_predictor.predict_opportunity(
                        prices.iloc[:i],
                        opportunity_predictor.volatility_history[f"{token0}_{token1}"],
                        opportunity_predictor.correlation_history[f"{token0}_{token1}"],
                        opportunity_predictor.market_history[f"{token0}_{token1}"]
                    )['confidence']
                    for i in range(len(prices))
                ]
            }, index=prices.index)
            
            st.plotly_chart(create_opportunity_chart(opportunities))
            
            st.subheader("3D Price Analysis")
            price_surface = pd.DataFrame(
                np.random.rand(10, 10),
                index=pd.date_range(end=datetime.now(), periods=10, freq='H'),
                columns=config['dexes'].keys()
            )
