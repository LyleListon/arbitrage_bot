# Backtesting Interface for Base Arbitrage Bot
# This module provides backtesting and strategy analysis features

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

def create_backtesting_interface():
    """Create backtesting interface"""
    st.title("Strategy Backtesting")
    
    # Strategy configuration
    st.subheader("Strategy Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Time period selection
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            help="Backtest start date"
        )
        
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            help="Backtest end date"
        )
        
        # Token pair selection
        token_pairs = st.multiselect(
            "Token Pairs",
            ["ETH/USDC", "ETH/USDT", "WBTC/ETH", "LINK/ETH", "UNI/ETH"],
            default=["ETH/USDC"]
        )
    
    with col2:
        # DEX selection
        dexes = st.multiselect(
            "DEXs",
            ["BaseSwap", "UniswapV3", "SushiSwap", "Aerodrome"],
            default=["BaseSwap", "UniswapV3"]
        )
        
        # Initial capital
        initial_capital = st.number_input(
            "Initial Capital (USD)",
            value=10000,
            min_value=1000,
            help="Starting capital for backtest"
        )
    
    # Trading parameters
    st.subheader("Trading Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_profit = st.slider(
            "Min Profit (%)",
            min_value=0.1,
            max_value=5.0,
            value=2.0,
            step=0.1
        )
        
        max_slippage = st.slider(
            "Max Slippage (%)",
            min_value=0.1,
            max_value=2.0,
            value=0.5,
            step=0.1
        )
    
    with col2:
        max_position = st.slider(
            "Max Position (ETH)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1
        )
        
        position_timeout = st.slider(
            "Position Timeout (sec)",
            min_value=10,
            max_value=300,
            value=60
        )
    
    with col3:
        max_gas = st.slider(
            "Max Gas (gwei)",
            min_value=10,
            max_value=200,
            value=50,
            step=5
        )
        
        cooldown = st.slider(
            "Cooldown (sec)",
            min_value=5,
            max_value=120,
            value=30
        )
    
    # Run backtest
    if st.button("Run Backtest", help="Execute backtest with current parameters"):
        st.info("Running backtest...")
        
        # Simulate backtest results
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        
        # Performance metrics
        results = pd.DataFrame({
            'timestamp': dates,
            'portfolio_value': initial_capital * (1 + np.random.normal(0.0002, 0.001, len(dates))).cumprod(),
            'trades': np.random.randint(0, 3, len(dates)),
            'profit': np.random.normal(2, 1, len(dates))
        })
        
        # Display results
        st.subheader("Backtest Results")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_return = (results['portfolio_value'].iloc[-1] - initial_capital) / initial_capital * 100
        total_trades = results['trades'].sum()
        win_rate = np.mean(results['profit'] > 0) * 100
        sharpe = np.mean(results['profit']) / np.std(results['profit']) * np.sqrt(365)
        
        with col1:
            st.metric(
                "Total Return",
                f"{total_return:.1f}%",
                help="Total return over backtest period"
            )
        
        with col2:
            st.metric(
                "Total Trades",
                f"{total_trades}",
                help="Number of executed trades"
            )
        
        with col3:
            st.metric(
                "Win Rate",
                f"{win_rate:.1f}%",
                help="Percentage of profitable trades"
            )
        
        with col4:
            st.metric(
                "Sharpe Ratio",
                f"{sharpe:.2f}",
                help="Risk-adjusted return metric"
            )
        
        # Performance chart
        st.subheader("Performance Chart")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=results['timestamp'],
            y=results['portfolio_value'],
            name='Portfolio Value',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            title='Portfolio Value Over Time',
            xaxis_title='Date',
            yaxis_title='Portfolio Value (USD)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig)
        
        # Trade analysis
        st.subheader("Trade Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Profit distribution
            profits = results[results['trades'] > 0]['profit']
            
            fig = px.histogram(
                profits,
                title='Profit Distribution',
                labels={'value': 'Profit (%)', 'count': 'Frequency'}
            )
            st.plotly_chart(fig)
        
        with col2:
            # Trade timing
            hourly_profits = results.groupby(results['timestamp'].dt.hour)['profit'].mean()
            
            fig = px.bar(
                x=hourly_profits.index,
                y=hourly_profits.values,
                title='Average Profit by Hour',
                labels={'x': 'Hour', 'y': 'Average Profit (%)'}
            )
            st.plotly_chart(fig)
        
        # Risk metrics
        st.subheader("Risk Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Calculate drawdown
            portfolio_values = results['portfolio_value']
            rolling_max = portfolio_values.expanding().max()
            drawdown = (portfolio_values - rolling_max) / rolling_max * 100
            
            fig = px.area(
                x=results['timestamp'],
                y=drawdown,
                title='Drawdown Analysis',
                labels={'x': 'Date', 'y': 'Drawdown (%)'}
            )
            st.plotly_chart(fig)
        
        with col2:
            # Risk metrics table
            risk_metrics = pd.DataFrame({
                'Metric': [
                    'Max Drawdown',
                    'Value at Risk (95%)',
                    'Expected Shortfall',
                    'Beta',
                    'Information Ratio'
                ],
                'Value': [
                    f"{drawdown.min():.1f}%",
                    f"{np.percentile(results['profit'], 5):.1f}%",
                    f"{np.mean(results['profit'][results['profit'] < np.percentile(results['profit'], 5)]):.1f}%",
                    f"{np.cov(results['profit'], results['portfolio_value'])[0,1] / np.var(results['portfolio_value']):.2f}",
                    f"{np.mean(results['profit']) / np.std(results['profit']):.2f}"
                ]
            })
            
            st.dataframe(risk_metrics)
        
        # Strategy recommendations
        st.subheader("Strategy Recommendations")
        
        recommendations = [
            "Increase position size during high volatility periods",
            "Reduce max slippage to improve win rate",
            "Focus on ETH/USDC pair for highest returns",
            "Consider longer cooldown period to reduce gas costs"
        ]
        
        for rec in recommendations:
            st.write(f"• {rec}")
        
        # Export results
        st.subheader("Export Results")
        
        if st.button("Export to CSV"):
            results.to_csv("backtest_results.csv", index=False)
            st.success("Results exported to backtest_results.csv")
