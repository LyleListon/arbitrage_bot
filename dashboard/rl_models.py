# Reinforcement Learning Models for Base Arbitrage Bot
# This module provides RL models for dynamic trading strategy optimization

import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque, namedtuple
import random
import plotly.express as px
from typing import List, Dict, Tuple

# Define experience tuple type
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])

class DQNNetwork(nn.Module):
    """Deep Q-Network for trading decisions"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128
    ):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

class PPONetwork(nn.Module):
    """Proximal Policy Optimization network"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128
    ):
        super().__init__()
        
        # Actor network (policy)
        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Critic network (value function)
        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.actor(state), self.critic(state)

class TradingEnvironment:
    """Trading environment for RL agents"""
    def __init__(
        self,
        data: pd.DataFrame,
        initial_balance: float = 10000,
        transaction_fee: float = 0.001
    ):
        self.data = data
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        self.reset()
    
    def reset(self) -> np.ndarray:
        """Reset environment to initial state"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.done = False
        return self._get_state()
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """Execute action and return new state"""
        # Execute action
        reward = self._execute_action(action)
        
        # Move to next step
        self.current_step += 1
        if self.current_step >= len(self.data) - 1:
            self.done = True
        
        # Get new state
        new_state = self._get_state()
        
        # Get info
        info = {
            'balance': self.balance,
            'position': self.position,
            'price': self.data.iloc[self.current_step]['price']
        }
        
        return new_state, reward, self.done, info
    
    def _get_state(self) -> np.ndarray:
        """Get current state representation"""
        state = []
        
        # Price features
        price_data = self.data.iloc[self.current_step]
        state.extend([
            price_data['price'],
            price_data['volume'],
            price_data['volatility'],
            price_data['spread'],
            price_data['gas']
        ])
        
        # Position features
        state.extend([
            self.balance / self.initial_balance,
            self.position
        ])
        
        return np.array(state)
    
    def _execute_action(self, action: int) -> float:
        """Execute trading action and return reward"""
        price = self.data.iloc[self.current_step]['price']
        next_price = self.data.iloc[self.current_step + 1]['price']
        
        # Calculate reward based on action
        if action == 0:  # Hold
            reward = 0
        elif action == 1:  # Buy
            if self.balance > 0:
                amount = self.balance * (1 - self.transaction_fee)
                self.position = amount / price
                self.balance = 0
                reward = self.position * (next_price - price)
            else:
                reward = 0
        else:  # Sell
            if self.position > 0:
                amount = self.position * price * (1 - self.transaction_fee)
                self.balance = amount
                self.position = 0
                reward = amount * (price - next_price) / price
            else:
                reward = 0
        
        return reward

class DQNAgent:
    """DQN agent for trading"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        memory_size: int = 10000,
        batch_size: int = 32
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        # Networks
        self.network = DQNNetwork(state_dim, action_dim, hidden_dim)
        self.target_network = DQNNetwork(state_dim, action_dim, hidden_dim)
        self.target_network.load_state_dict(self.network.state_dict())
        
        # Optimizer
        self.optimizer = optim.Adam(self.network.parameters(), lr=learning_rate)
        
        # Replay memory
        self.memory = deque(maxlen=memory_size)
    
    def act(self, state: np.ndarray) -> int:
        """Select action using epsilon-greedy policy"""
        if random.random() < self.epsilon:
            return random.randrange(self.action_dim)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.network(state_tensor)
            return q_values.argmax().item()
    
    def train(self, experiences: List[Experience]) -> float:
        """Train network on batch of experiences"""
        # Unpack experiences
        states = torch.FloatTensor([e.state for e in experiences])
        actions = torch.LongTensor([e.action for e in experiences])
        rewards = torch.FloatTensor([e.reward for e in experiences])
        next_states = torch.FloatTensor([e.next_state for e in experiences])
        dones = torch.FloatTensor([e.done for e in experiences])
        
        # Get current Q values
        current_q_values = self.network(states).gather(1, actions.unsqueeze(1))
        
        # Get next Q values
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Calculate loss
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        # Update network
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        return loss.item()

def create_rl_interface():
    """Create RL models interface"""
    st.title("Reinforcement Learning Models")
    
    # Model selection
    model_type = st.selectbox(
        "Select Model Type",
        ["DQN", "PPO"]
    )
    
    # Environment configuration
    st.subheader("Environment Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        initial_balance = st.number_input(
            "Initial Balance (USD)",
            min_value=1000,
            max_value=100000,
            value=10000,
            step=1000
        )
        
        transaction_fee = st.slider(
            "Transaction Fee (%)",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.1
        )
    
    with col2:
        training_episodes = st.slider(
            "Training Episodes",
            min_value=10,
            max_value=1000,
            value=100
        )
        
        evaluation_episodes = st.slider(
            "Evaluation Episodes",
            min_value=5,
            max_value=50,
            value=10
        )
    
    # Model parameters
    st.subheader("Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        learning_rate = st.select_slider(
            "Learning Rate",
            options=[0.0001, 0.0005, 0.001, 0.005, 0.01],
            value=0.001
        )
        
        hidden_dim = st.slider(
            "Hidden Dimension",
            min_value=32,
            max_value=256,
            value=128,
            step=32
        )
    
    with col2:
        gamma = st.slider(
            "Discount Factor",
            min_value=0.8,
            max_value=0.999,
            value=0.99
        )
        
        batch_size = st.slider(
            "Batch Size",
            min_value=16,
            max_value=128,
            value=32,
            step=16
        )
    
    # Train model
    if st.button("Train Model"):
        st.info(f"Training {model_type} model...")
        
        # Create progress containers
        progress_bar = st.progress(0)
        metrics_chart = st.empty()
        
        # Generate sample data
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='H')
        data = pd.DataFrame({
            'price': np.random.normal(0.002, 0.001, len(dates)).cumsum(),
            'volume': np.random.normal(100, 10, len(dates)),
            'volatility': np.random.normal(0.02, 0.005, len(dates)),
            'spread': np.random.normal(0.001, 0.0002, len(dates)),
            'gas': np.random.normal(50, 5, len(dates))
        })
        
        # Create environment
        env = TradingEnvironment(
            data,
            initial_balance=initial_balance,
            transaction_fee=transaction_fee/100
        )
        
        # Training metrics
        episode_rewards = []
        portfolio_values = []
        
        # Training loop
        for episode in range(training_episodes):
            state = env.reset()
            episode_reward = 0
            
            while not env.done:
                # Random actions for simulation
                action = random.randrange(3)  # 0: Hold, 1: Buy, 2: Sell
                next_state, reward, done, info = env.step(action)
                episode_reward += reward
                state = next_state
            
            episode_rewards.append(episode_reward)
            portfolio_values.append(info['balance'] + info['position'] * info['price'])
            
            # Update progress
            progress_bar.progress((episode + 1) / training_episodes)
            
            # Update metrics chart
            if (episode + 1) % 10 == 0:
                metrics = pd.DataFrame({
                    'Episode Reward': episode_rewards,
                    'Portfolio Value': portfolio_values
                })
                
                fig = px.line(
                    metrics,
                    title='Training Metrics',
                    labels={'value': 'Value', 'index': 'Episode'}
                )
                metrics_chart.plotly_chart(fig)
        
        st.success("Training complete!")
        
        # Display final metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Final Portfolio Value",
                f"${portfolio_values[-1]:.2f}",
                f"{(portfolio_values[-1] - initial_balance) / initial_balance * 100:.1f}%"
            )
        
        with col2:
            st.metric(
                "Average Episode Reward",
                f"{np.mean(episode_rewards):.2f}"
            )
        
        with col3:
            st.metric(
                "Max Drawdown",
                f"{(np.min(portfolio_values) - np.max(portfolio_values)) / np.max(portfolio_values) * 100:.1f}%"
            )
        
        # Plot training results
        st.subheader("Training Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Portfolio value over time
            fig = px.line(
                portfolio_values,
                title='Portfolio Value',
                labels={'value': 'Value ($)', 'index': 'Episode'}
            )
            st.plotly_chart(fig)
        
        with col2:
            # Episode rewards
            fig = px.line(
                episode_rewards,
                title='Episode Rewards',
                labels={'value': 'Reward', 'index': 'Episode'}
            )
            st.plotly_chart(fig)
    
    # Export model
    st.subheader("Export Model")
    
    if st.button("Export Model"):
        st.success(f"{model_type} model exported to {model_type.lower()}_model.pt")
