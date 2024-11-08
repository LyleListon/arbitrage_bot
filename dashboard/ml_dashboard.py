import os
import sys
import logging
from datetime import datetime
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# Load configuration
config_path = os.path.join(parent_dir, 'config.json')
try:
    with open(config_path, 'r') as f:
        config = json.load(f)
    logging.info(f"Configuration loaded successfully from {config_path}")
except FileNotFoundError:
    st.error(f"Configuration file not found: {config_path}")
    logging.error(f"Configuration file not found: {config_path}")
    st.stop()
except json.JSONDecodeError:
    st.error(f"Invalid JSON in configuration file: {config_path}")
    logging.error(f"Invalid JSON in configuration file: {config_path}")
    st.stop()

# Import predictors
try:
    from scripts.ml_predictor import MLPredictor
    from scripts.opportunity_predictor import OpportunityPredictor
    from scripts.arbitrage_bot import ArbitrageBot
    logging.info("ML and Opportunity predictors imported successfully")
except ImportError as e:
    st.error(f"Failed to import predictor modules: {str(e)}")
    logging.error(f"Failed to import predictor modules: {str(e)}")
    st.stop()

# Initialize predictors and bot
try:
    ml_predictor = MLPredictor(config_path)
    opportunity_predictor = OpportunityPredictor(config_path)
    arbitrage_bot = ArbitrageBot(config_path)
    logging.info("Predictors and bot initialized successfully")
except Exception as e:
    st.error(f"Failed to initialize predictors or bot: {str(e)}")
    logging.error(f"Failed to initialize predictors or bot: {str(e)}")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Base Arbitrage ML Dashboard",
    page_icon="📊",
    layout="wide"
)

# Helper functions for visualizations
def create_price_chart(prices: pd.DataFrame, predictions: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices.index, y=prices['price'], name='Actual Price', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=predictions.index, y=predictions['price_prediction'], name='Predicted Price', line=dict(color='red', dash='dash')))
    fig.update_layout(title='Price History and Predictions', xaxis_title='Time', yaxis_title='Price')
    return fig

def create_opportunity_chart(opportunities: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=opportunities.index, y=opportunities['confidence'], name='Confidence', line=dict(color='green')))
    fig.add_hline(y=0.8, line_dash="dash", line_color="red", annotation_text="Confidence Threshold (80%)")
    fig.update_layout(title='Arbitrage Opportunity Confidence', xaxis_title='Time', yaxis_title='Confidence', yaxis_range=[0, 1])
    return fig

def create_model_metrics_chart(metrics: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for col in metrics.columns:
        fig.add_trace(go.Scatter(x=metrics.index, y=metrics[col], name=col, mode='lines+markers'))
    fig.update_layout(title='Model Performance Metrics', xaxis_title='Time', yaxis_title='Metric Value')
    return fig

# Function to fetch real-time data
async def fetch_real_time_data(token_pair: str):
    # Fetch price data
    price_data = await opportunity_predictor.get_price_data(token_pair)
    
    # Fetch volatility data
    volatility_data = await opportunity_predictor.get_volatility_data(token_pair)
    
    # Fetch correlation data
    correlation_data = await opportunity_predictor.get_correlation_data(token_pair)
    
    # Fetch market data
    market_data = await opportunity_predictor.get_market_data(token_pair)
    
    # Get ML predictions
    prediction = ml_predictor.predict_opportunity(
        price_data,
        volatility_data,
        correlation_data,
        market_data
    )
    
    # Fetch opportunities
    opportunities = await opportunity_predictor.predict_opportunities()
    
    # Create opportunities DataFrame with 'confidence' column
    if opportunities:
        opportunities_df = pd.DataFrame([
            {
                'timestamp': datetime.fromisoformat(opp['timestamp']),
                'confidence': opp['prediction']['confidence'],
                'token0': opp['token0'],
                'token1': opp['token1'],
                'price_prediction': opp['prediction']['price_prediction'],
                'opportunity_probability': opp['prediction']['opportunity_probability'],
                'spread_prediction': opp['prediction']['spread_prediction']
            } for opp in opportunities
        ]).set_index('timestamp')
    else:
        opportunities_df = pd.DataFrame(columns=['confidence', 'token0', 'token1', 'price_prediction', 'opportunity_probability', 'spread_prediction'])
        opportunities_df.index.name = 'timestamp'
    
    # Get model metrics
    model_metrics = ml_predictor.get_model_metrics()
    
    return {
        'price_data': price_data,
        'prediction': prediction,
        'opportunities': opportunities_df,
        'model_metrics': model_metrics
    }

# Main dashboard content
def main():
    st.title("Base Arbitrage ML Dashboard")
    
    # Sidebar for user inputs and bot control
    st.sidebar.header("Settings")
    token_pair = st.sidebar.selectbox("Select Token Pair", [f"{t1}/{t2}" for t1 in config['tokens'] for t2 in config['tokens'] if t1 != t2])
    
    # Bot control
    st.sidebar.header("Bot Control")
    bot_active = st.sidebar.toggle("Activate Bot", value=False)
    
    if bot_active:
        arbitrage_bot.start()
        st.sidebar.success("Bot is active and running")
    else:
        arbitrage_bot.stop()
        st.sidebar.warning("Bot is inactive")
    
    # Bot status
    st.sidebar.header("Bot Status")
    bot_status = arbitrage_bot.get_status()
    st.sidebar.write(f"Status: {'Running' if bot_status['is_running'] else 'Stopped'}")
    st.sidebar.write(f"Current thought: {bot_status['current_thought']}")
    st.sidebar.write(f"Last update: {bot_status['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Fetch real-time data
    data = asyncio.run(fetch_real_time_data(token_pair))
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Price Analysis")
        price_data = data['price_data']
        predictions = pd.DataFrame({'price_prediction': [data['prediction']['price_prediction']]}, index=[price_data.index[-1]])
        st.plotly_chart(create_price_chart(price_data, predictions))
        
        st.subheader("Model Performance")
        st.plotly_chart(create_model_metrics_chart(data['model_metrics']))
    
    with col2:
        st.subheader("Opportunity Analysis")
        st.plotly_chart(create_opportunity_chart(data['opportunities']))
        
        st.subheader("Recent Opportunities")
        if not data['opportunities'].empty:
            recent_opps = data['opportunities'].sort_index(ascending=False).head(5).reset_index()
            recent_opps['timestamp'] = recent_opps['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            st.table(recent_opps[['timestamp', 'token0', 'token1', 'confidence', 'spread_prediction']])
        else:
            st.write("No opportunities found.")
    
    # Bottom section - Key Metrics
    st.subheader("Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    latest_price = price_data['price'].iloc[-1]
    prev_price = price_data['price'].iloc[-2]
    latest_pred = data['prediction']['price_prediction']
    col1.metric("Current Price", f"${latest_price:.2f}", f"{(latest_price - prev_price) / prev_price:.2%}")
    col2.metric("Predicted Price", f"${latest_pred:.2f}", f"{(latest_pred - latest_price) / latest_price:.2%}")
    col3.metric("Opportunity Confidence", f"{data['prediction']['confidence']:.2%}", f"{(data['prediction']['confidence'] - 0.8) * 100:.2f}%")
    col4.metric("Model Accuracy", f"{data['model_metrics']['RF Accuracy'].iloc[-1]:.2%}", f"{(data['model_metrics']['RF Accuracy'].iloc[-1] - data['model_metrics']['RF Accuracy'].iloc[-2]) * 100:.2f}%")

    # Auto-refresh functionality
    if st.button("Refresh Data"):
        st.experimental_rerun()
    
    st.sidebar.write("Last update: ", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()
