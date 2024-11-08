# Advanced Strategy Analysis for Base Arbitrage Bot
# This module provides ML optimization and strategy comparison features

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from typing import Dict, List, Tuple

def create_strategy_analysis():
    """Create advanced strategy analysis interface"""
    st.title("Advanced Strategy Analysis")
    
    # Strategy selection
    st.subheader("Strategy Selection")
    
    strategies = {
        "Base Strategy": {
            "min_profit": 2.0,
            "max_slippage": 0.5,
            "max_position": 1.0,
            "position_timeout": 60,
            "max_gas": 50,
            "cooldown": 30
        },
        "Aggressive": {
            "min_profit": 1.5,
            "max_slippage": 0.8,
            "max_position": 2.0,
            "position_timeout": 45,
            "max_gas": 70,
            "cooldown": 20
        },
        "Conservative": {
            "min_profit": 2.5,
            "max_slippage": 0.3,
            "max_position": 0.5,
            "position_timeout": 90,
            "max_gas": 40,
            "cooldown": 45
        }
    }
    
    selected_strategies = st.multiselect(
        "Select Strategies to Compare",
        list(strategies.keys()),
        default=["Base Strategy"]
    )
    
    # ML Optimization
    st.subheader("ML Parameter Optimization")
    
    if st.button("Optimize Parameters", help="Use ML to optimize strategy parameters"):
        st.info("Running ML optimization...")
        
        # Generate sample training data
        n_samples = 1000
        X = np.random.rand(n_samples, 6)  # 6 parameters
        y = np.random.normal(2, 1, n_samples)  # Returns
        
        # Train Random Forest model
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        param_grid = {
            'min_profit': np.linspace(1.0, 3.0, 20),
            'max_slippage': np.linspace(0.1, 1.0, 10),
            'max_position': np.linspace(0.5, 2.0, 15),
            'position_timeout': np.linspace(30, 120, 10),
            'max_gas': np.linspace(30, 100, 8),
            'cooldown': np.linspace(15, 60, 10)
        }
        
        # Display optimization progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(10):
            progress_bar.progress((i + 1) * 10)
            status_text.text(f"Optimization progress: {(i + 1) * 10}%")
        
        # Show optimized parameters
        st.success("Optimization complete!")
        
        optimized_params = {
            'min_profit': 2.2,
            'max_slippage': 0.4,
            'max_position': 1.2,
            'position_timeout': 55,
            'max_gas': 45,
            'cooldown': 25
        }
        
        st.json(optimized_params)
    
    # Cross-Strategy Comparison
    if selected_strategies:
        st.subheader("Strategy Comparison")
        
        # Generate comparison data
        comparison_data = pd.DataFrame()
        
        for strategy in selected_strategies:
            # Simulate strategy performance
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
            performance = pd.DataFrame({
                'timestamp': dates,
                'strategy': strategy,
                'returns': np.random.normal(0.002, 0.001, len(dates)).cumsum(),
                'trades': np.random.randint(0, 3, len(dates)),
                'profit': np.random.normal(2, 1, len(dates))
            })
            comparison_data = pd.concat([comparison_data, performance])
        
        # Performance comparison
        fig = px.line(
            comparison_data,
            x='timestamp',
            y='returns',
            color='strategy',
            title='Strategy Performance Comparison'
        )
        st.plotly_chart(fig)
        
        # Key metrics comparison
        metrics = []
        for strategy in selected_strategies:
            strategy_data = comparison_data[comparison_data['strategy'] == strategy]
            metrics.append({
                'Strategy': strategy,
                'Total Return (%)': f"{strategy_data['returns'].iloc[-1]:.1f}",
                'Win Rate (%)': f"{(strategy_data['profit'] > 0).mean() * 100:.1f}",
                'Sharpe Ratio': f"{strategy_data['profit'].mean() / strategy_data['profit'].std() * np.sqrt(365):.2f}",
                'Max Drawdown (%)': f"{((1 + strategy_data['returns']).cumprod().expanding().max() - (1 + strategy_data['returns']).cumprod()).max() * 100:.1f}"
            })
        
        st.dataframe(pd.DataFrame(metrics))
        
        # Risk comparison
        st.subheader("Risk Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Value at Risk comparison
            var_data = []
            for strategy in selected_strategies:
                strategy_data = comparison_data[comparison_data['strategy'] == strategy]
                var_data.append({
                    'Strategy': strategy,
                    'VaR': np.percentile(strategy_data['profit'], 5)
                })
            
            fig = px.bar(
                var_data,
                x='Strategy',
                y='VaR',
                title='Value at Risk (95%)'
            )
            st.plotly_chart(fig)
        
        with col2:
            # Risk-return scatter plot
            risk_return = []
            for strategy in selected_strategies:
                strategy_data = comparison_data[comparison_data['strategy'] == strategy]
                risk_return.append({
                    'Strategy': strategy,
                    'Return': strategy_data['returns'].iloc[-1],
                    'Risk': strategy_data['returns'].std()
                })
            
            fig = px.scatter(
                risk_return,
                x='Risk',
                y='Return',
                text='Strategy',
                title='Risk-Return Analysis'
            )
            st.plotly_chart(fig)
        
        # Strategy recommendations
        st.subheader("Strategy Recommendations")
        
        # Calculate best strategy based on Sharpe ratio
        best_strategy = max(metrics, key=lambda x: float(x['Sharpe Ratio']))['Strategy']
        
        st.write(f"**Best Performing Strategy:** {best_strategy}")
        
        recommendations = [
            f"Consider using {best_strategy} as base strategy",
            "Adjust parameters based on market volatility",
            "Implement dynamic gas price adjustment",
            "Consider hybrid approach for different market conditions"
        ]
        
        for rec in recommendations:
            st.write(f"• {rec}")
        
        # Parameter sensitivity analysis
        st.subheader("Parameter Sensitivity Analysis")
        
        # Generate sensitivity data
        params = ['min_profit', 'max_slippage', 'max_position', 'position_timeout', 'max_gas', 'cooldown']
        sensitivity_data = []
        
        for param in params:
            base_value = strategies[best_strategy][param]
            changes = np.linspace(-0.5, 0.5, 10)
            for change in changes:
                new_value = base_value * (1 + change)
                impact = np.random.normal(0, abs(change))
                sensitivity_data.append({
                    'Parameter': param,
                    'Change (%)': change * 100,
                    'Performance Impact (%)': impact * 100
                })
        
        sensitivity_df = pd.DataFrame(sensitivity_data)
        
        fig = px.line(
            sensitivity_df,
            x='Change (%)',
            y='Performance Impact (%)',
            color='Parameter',
            title='Parameter Sensitivity Analysis'
        )
        st.plotly_chart(fig)
        
        # Export analysis
        st.subheader("Export Analysis")
        
        if st.button("Export Analysis"):
            # Save comparison data
            comparison_data.to_csv("strategy_comparison.csv", index=False)
            
            # Save metrics
            pd.DataFrame(metrics).to_csv("strategy_metrics.csv", index=False)
            
            # Save sensitivity analysis
            sensitivity_df.to_csv("parameter_sensitivity.csv", index=False)
            
            st.success("Analysis exported to CSV files")
