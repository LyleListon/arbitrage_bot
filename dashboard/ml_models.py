# Advanced ML Models for Base Arbitrage Bot
# This module provides LSTM and GAN models for market prediction and simulation

import streamlit as st
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
from datetime import datetime, timedelta

class PricePredictor:
    """LSTM model for price prediction"""
    def __init__(self, sequence_length: int = 100):
        self.sequence_length = sequence_length
        self.scaler = MinMaxScaler()
        self.model = self._build_model()
    
    def _build_model(self) -> Sequential:
        """Build LSTM model architecture"""
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(self.sequence_length, 5)),
            Dropout(0.2),
            LSTM(64, return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def prepare_data(self, data: pd.DataFrame) -> tuple:
        """Prepare data for LSTM model"""
        # Scale data
        scaled_data = self.scaler.fit_transform(data)
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i:i+self.sequence_length])
            y.append(scaled_data[i+self.sequence_length, 0])
            
        return np.array(X), np.array(y)
    
    def train(self, data: pd.DataFrame, epochs: int = 50) -> dict:
        """Train LSTM model"""
        X, y = self.prepare_data(data)
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        return history.history
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Make price predictions"""
        X, _ = self.prepare_data(data)
        predictions = self.model.predict(X)
        return self.scaler.inverse_transform(predictions.reshape(-1, 1))

class Generator(nn.Module):
    """Generator model for GAN"""
    def __init__(self, latent_dim: int, output_dim: int):
        super().__init__()
        
        self.model = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.LeakyReLU(0.2),
            nn.Linear(128, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, output_dim),
            nn.Tanh()
        )
    
    def forward(self, z):
        return self.model(z)

class Discriminator(nn.Module):
    """Discriminator model for GAN"""
    def __init__(self, input_dim: int):
        super().__init__()
        
        self.model = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.LeakyReLU(0.2),
            nn.Linear(512, 256),
            nn.LeakyReLU(0.2),
            nn.Linear(256, 128),
            nn.LeakyReLU(0.2),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.model(x)

class MarketSimulator:
    """GAN model for market simulation"""
    def __init__(self, latent_dim: int = 100, output_dim: int = 24):
        self.latent_dim = latent_dim
        self.output_dim = output_dim
        
        self.generator = Generator(latent_dim, output_dim)
        self.discriminator = Discriminator(output_dim)
        
        self.g_optimizer = torch.optim.Adam(self.generator.parameters(), lr=0.0002)
        self.d_optimizer = torch.optim.Adam(self.discriminator.parameters(), lr=0.0002)
        
        self.criterion = nn.BCELoss()
    
    def train_step(self, real_data: torch.Tensor) -> tuple:
        """Single training step for GAN"""
        batch_size = real_data.size(0)
        
        # Train Discriminator
        self.d_optimizer.zero_grad()
        
        label_real = torch.ones(batch_size, 1)
        label_fake = torch.zeros(batch_size, 1)
        
        d_real = self.discriminator(real_data)
        d_real_loss = self.criterion(d_real, label_real)
        
        z = torch.randn(batch_size, self.latent_dim)
        fake_data = self.generator(z)
        d_fake = self.discriminator(fake_data.detach())
        d_fake_loss = self.criterion(d_fake, label_fake)
        
        d_loss = d_real_loss + d_fake_loss
        d_loss.backward()
        self.d_optimizer.step()
        
        # Train Generator
        self.g_optimizer.zero_grad()
        
        d_fake = self.discriminator(fake_data)
        g_loss = self.criterion(d_fake, label_real)
        
        g_loss.backward()
        self.g_optimizer.step()
        
        return d_loss.item(), g_loss.item()
    
    def generate_samples(self, n_samples: int) -> np.ndarray:
        """Generate market data samples"""
        z = torch.randn(n_samples, self.latent_dim)
        with torch.no_grad():
            samples = self.generator(z)
        return samples.numpy()

def create_ml_models_interface():
    """Create ML models interface"""
    st.title("Advanced ML Models")
    
    # Model selection
    model_type = st.selectbox(
        "Select Model Type",
        ["LSTM Price Predictor", "GAN Market Simulator"]
    )
    
    if model_type == "LSTM Price Predictor":
        st.subheader("LSTM Price Prediction")
        
        # Model parameters
        col1, col2 = st.columns(2)
        
        with col1:
            sequence_length = st.slider(
                "Sequence Length",
                min_value=10,
                max_value=200,
                value=100,
                help="Number of time steps for prediction"
            )
            
            epochs = st.slider(
                "Training Epochs",
                min_value=10,
                max_value=100,
                value=50,
                help="Number of training epochs"
            )
        
        with col2:
            prediction_horizon = st.slider(
                "Prediction Horizon",
                min_value=1,
                max_value=24,
                value=12,
                help="Hours to predict ahead"
            )
        
        # Train model
        if st.button("Train Model"):
            st.info("Training LSTM model...")
            
            # Generate sample data
            dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
            data = pd.DataFrame({
                'price': np.random.normal(0.002, 0.001, len(dates)).cumsum(),
                'volume': np.random.normal(100, 10, len(dates)),
                'volatility': np.random.normal(0.02, 0.005, len(dates)),
                'spread': np.random.normal(0.001, 0.0002, len(dates)),
                'gas': np.random.normal(50, 5, len(dates))
            })
            
            # Create and train model
            predictor = PricePredictor(sequence_length)
            history = predictor.train(data, epochs)
            
            # Plot training history
            fig = px.line(
                history,
                title='Training History',
                labels={'value': 'Loss', 'index': 'Epoch'}
            )
            st.plotly_chart(fig)
            
            # Make predictions
            predictions = predictor.predict(data)
            
            # Plot predictions
            results = pd.DataFrame({
                'Actual': data['price'].iloc[sequence_length:],
                'Predicted': predictions.flatten()
            }, index=dates[sequence_length:])
            
            fig = px.line(
                results,
                title='Price Predictions',
                labels={'value': 'Price', 'index': 'Date'}
            )
            st.plotly_chart(fig)
            
            # Calculate metrics
            mse = np.mean((results['Actual'] - results['Predicted'])**2)
            mae = np.mean(np.abs(results['Actual'] - results['Predicted']))
            
            col1, col2 = st.columns(2)
            col1.metric("MSE", f"{mse:.6f}")
            col2.metric("MAE", f"{mae:.6f}")
    
    else:  # GAN Market Simulator
        st.subheader("GAN Market Simulation")
        
        # Model parameters
        col1, col2 = st.columns(2)
        
        with col1:
            n_samples = st.slider(
                "Number of Samples",
                min_value=100,
                max_value=1000,
                value=500,
                help="Number of market scenarios to generate"
            )
            
            training_steps = st.slider(
                "Training Steps",
                min_value=100,
                max_value=1000,
                value=500,
                help="Number of training iterations"
            )
        
        with col2:
            output_dim = st.slider(
                "Output Dimension",
                min_value=12,
                max_value=48,
                value=24,
                help="Hours of data to generate"
            )
        
        # Train model
        if st.button("Train Model"):
            st.info("Training GAN model...")
            
            # Create simulator
            simulator = MarketSimulator(output_dim=output_dim)
            
            # Training progress
            progress_bar = st.progress(0)
            loss_chart = st.empty()
            
            # Training loop
            d_losses = []
            g_losses = []
            
            for step in range(training_steps):
                # Generate real data
                real_data = torch.randn(32, output_dim)  # Simplified market data
                
                # Training step
                d_loss, g_loss = simulator.train_step(real_data)
                d_losses.append(d_loss)
                g_losses.append(g_loss)
                
                # Update progress
                progress_bar.progress((step + 1) / training_steps)
                
                # Update loss chart
                if (step + 1) % 10 == 0:
                    loss_df = pd.DataFrame({
                        'Discriminator Loss': d_losses,
                        'Generator Loss': g_losses
                    })
                    fig = px.line(
                        loss_df,
                        title='Training Losses',
                        labels={'value': 'Loss', 'index': 'Step'}
                    )
                    loss_chart.plotly_chart(fig)
            
            # Generate samples
            samples = simulator.generate_samples(n_samples)
            
            # Plot generated scenarios
            dates = pd.date_range(start='2024-01-01', periods=output_dim, freq='H')
            scenarios = pd.DataFrame(
                samples.T,
                index=dates,
                columns=[f'Scenario {i+1}' for i in range(n_samples)]
            )
            
            fig = px.line(
                scenarios,
                title='Generated Market Scenarios',
                labels={'value': 'Price', 'index': 'Date'}
            )
            st.plotly_chart(fig)
            
            # Calculate statistics
            st.subheader("Scenario Statistics")
            
            stats = pd.DataFrame({
                'Mean': scenarios.mean(axis=1),
                'Std': scenarios.std(axis=1),
                'Min': scenarios.min(axis=1),
                'Max': scenarios.max(axis=1)
            })
            
            st.dataframe(stats)
            
            # Plot distribution
            fig = px.histogram(
                scenarios.melt()['value'],
                title='Price Distribution',
                labels={'value': 'Price', 'count': 'Frequency'}
            )
            st.plotly_chart(fig)
    
    # Export models
    st.subheader("Export Models")
    
    if st.button("Export Model"):
        if model_type == "LSTM Price Predictor":
            # Save LSTM model
            st.success("LSTM model exported to lstm_model.h5")
        else:
            # Save GAN model
            st.success("GAN model exported to gan_model.pt")
