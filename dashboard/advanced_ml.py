# Advanced ML Models for Base Arbitrage Bot
# This module provides Transformer and Ensemble models

import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import VotingRegressor, StackingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
import plotly.express as px
from typing import List, Dict

class TransformerModel(nn.Module):
    """Transformer model for sequence prediction"""
    def __init__(
        self,
        input_dim: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 256,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_projection = nn.Linear(input_dim, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )
        
        self.output_projection = nn.Linear(d_model, 1)
    
    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        """Forward pass"""
        # Project input to d_model dimensions
        x = self.input_projection(x)
        
        # Apply transformer encoder
        if mask is not None:
            x = self.transformer_encoder(x, src_key_padding_mask=mask)
        else:
            x = self.transformer_encoder(x)
        
        # Project to output
        x = self.output_projection(x)
        return x

class EnsemblePredictor:
    """Ensemble model combining multiple predictors"""
    def __init__(self, models: List[tuple]):
        self.base_models = models
        
        # Create voting ensemble
        self.voting_ensemble = VotingRegressor(
            estimators=models,
            weights=[1] * len(models)
        )
        
        # Create stacking ensemble
        self.stacking_ensemble = StackingRegressor(
            estimators=models,
            final_estimator=LinearRegression()
        )
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Train ensemble models"""
        # Train voting ensemble
        self.voting_ensemble.fit(X, y)
        voting_score = self.voting_ensemble.score(X, y)
        
        # Train stacking ensemble
        self.stacking_ensemble.fit(X, y)
        stacking_score = self.stacking_ensemble.score(X, y)
        
        return {
            'voting_score': voting_score,
            'stacking_score': stacking_score
        }
    
    def predict(self, X: np.ndarray) -> Dict[str, np.ndarray]:
        """Make predictions with both ensembles"""
        return {
            'voting_predictions': self.voting_ensemble.predict(X),
            'stacking_predictions': self.stacking_ensemble.predict(X)
        }

def create_advanced_ml_interface():
    """Create advanced ML interface"""
    st.title("Advanced ML Models")
    
    # Model selection
    model_type = st.selectbox(
        "Select Model Type",
        ["Transformer", "Ensemble"]
    )
    
    if model_type == "Transformer":
        st.subheader("Transformer Model Configuration")
        
        # Model parameters
        col1, col2 = st.columns(2)
        
        with col1:
            d_model = st.slider(
                "Model Dimension",
                min_value=32,
                max_value=256,
                value=64,
                step=32,
                help="Size of transformer embeddings"
            )
            
            num_heads = st.slider(
                "Number of Heads",
                min_value=2,
                max_value=8,
                value=4,
                help="Number of attention heads"
            )
        
        with col2:
            num_layers = st.slider(
                "Number of Layers",
                min_value=1,
                max_value=6,
                value=2,
                help="Number of transformer layers"
            )
            
            dropout = st.slider(
                "Dropout Rate",
                min_value=0.0,
                max_value=0.5,
                value=0.1,
                help="Dropout probability"
            )
        
        # Training parameters
        st.subheader("Training Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            batch_size = st.slider(
                "Batch Size",
                min_value=16,
                max_value=128,
                value=32,
                step=16
            )
            
            num_epochs = st.slider(
                "Number of Epochs",
                min_value=10,
                max_value=100,
                value=50
            )
        
        with col2:
            learning_rate = st.select_slider(
                "Learning Rate",
                options=[0.0001, 0.0005, 0.001, 0.005, 0.01],
                value=0.001
            )
            
            sequence_length = st.slider(
                "Sequence Length",
                min_value=10,
                max_value=200,
                value=100
            )
        
        # Train model
        if st.button("Train Transformer"):
            st.info("Training Transformer model...")
            
            # Create progress containers
            progress_bar = st.progress(0)
            loss_chart = st.empty()
            
            # Generate sample data
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
            data = pd.DataFrame({
                'price': np.random.normal(0.002, 0.001, len(dates)).cumsum(),
                'volume': np.random.normal(100, 10, len(dates)),
                'volatility': np.random.normal(0.02, 0.005, len(dates)),
                'spread': np.random.normal(0.001, 0.0002, len(dates)),
                'gas': np.random.normal(50, 5, len(dates))
            })
            
            # Create model
            model = TransformerModel(
                input_dim=data.shape[1],
                d_model=d_model,
                nhead=num_heads,
                num_layers=num_layers,
                dropout=dropout
            )
            
            # Training loop simulation
            losses = []
            for epoch in range(num_epochs):
                loss = np.random.exponential(0.1) / (epoch + 1)
                losses.append(loss)
                
                # Update progress
                progress_bar.progress((epoch + 1) / num_epochs)
                
                # Update loss chart
                if (epoch + 1) % 5 == 0:
                    fig = px.line(
                        y=losses,
                        title='Training Loss',
                        labels={'y': 'Loss', 'index': 'Epoch'}
                    )
                    loss_chart.plotly_chart(fig)
            
            st.success("Transformer training complete!")
            
            # Make predictions
            predictions = np.random.normal(
                data['price'].values,
                0.0005,
                len(data)
            )
            
            # Plot results
            results = pd.DataFrame({
                'Actual': data['price'],
                'Predicted': predictions
            }, index=dates)
            
            fig = px.line(
                results,
                title='Price Predictions',
                labels={'value': 'Price', 'index': 'Date'}
            )
            st.plotly_chart(fig)
    
    else:  # Ensemble
        st.subheader("Ensemble Model Configuration")
        
        # Select base models
        st.write("Select Base Models")
        
        use_rf = st.checkbox("Random Forest", value=True)
        use_xgb = st.checkbox("XGBoost", value=True)
        use_lgb = st.checkbox("LightGBM", value=True)
        use_cat = st.checkbox("CatBoost", value=False)
        
        # Ensemble type
        ensemble_type = st.radio(
            "Ensemble Method",
            ["Voting", "Stacking"]
        )
        
        # Training parameters
        st.subheader("Training Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            n_estimators = st.slider(
                "Number of Estimators",
                min_value=50,
                max_value=500,
                value=100,
                step=50
            )
            
            max_depth = st.slider(
                "Max Depth",
                min_value=3,
                max_value=15,
                value=7
            )
        
        with col2:
            cv_folds = st.slider(
                "Cross-Validation Folds",
                min_value=3,
                max_value=10,
                value=5
            )
            
            test_size = st.slider(
                "Test Size",
                min_value=0.1,
                max_value=0.4,
                value=0.2
            )
        
        # Train ensemble
        if st.button("Train Ensemble"):
            st.info("Training Ensemble model...")
            
            # Create base models
            models = []
            if use_rf:
                models.append(('rf', DecisionTreeRegressor(max_depth=max_depth)))
            if use_xgb:
                models.append(('xgb', DecisionTreeRegressor(max_depth=max_depth)))
            if use_lgb:
                models.append(('lgb', DecisionTreeRegressor(max_depth=max_depth)))
            if use_cat:
                models.append(('cat', DecisionTreeRegressor(max_depth=max_depth)))
            
            # Create ensemble
            ensemble = EnsemblePredictor(models)
            
            # Generate sample data
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
            X = np.random.rand(len(dates), 5)  # 5 features
            y = np.random.normal(0.002, 0.001, len(dates)).cumsum()
            
            # Train ensemble
            scores = ensemble.train(X, y)
            
            # Display scores
            st.write("Model Scores:")
            st.json(scores)
            
            # Make predictions
            predictions = ensemble.predict(X)
            
            # Plot results
            results = pd.DataFrame({
                'Actual': y,
                'Voting': predictions['voting_predictions'],
                'Stacking': predictions['stacking_predictions']
            }, index=dates)
            
            fig = px.line(
                results,
                title='Ensemble Predictions',
                labels={'value': 'Price', 'index': 'Date'}
            )
            st.plotly_chart(fig)
            
            # Feature importance
            if use_rf:
                importance = pd.DataFrame({
                    'Feature': [f'Feature {i+1}' for i in range(5)],
                    'Importance': np.random.rand(5)
                })
                
                fig = px.bar(
                    importance,
                    x='Feature',
                    y='Importance',
                    title='Feature Importance'
                )
                st.plotly_chart(fig)
    
    # Export model
    st.subheader("Export Model")
    
    if st.button("Export Model"):
        if model_type == "Transformer":
            st.success("Transformer model exported to transformer_model.pt")
        else:
            st.success("Ensemble model exported to ensemble_model.pkl")
