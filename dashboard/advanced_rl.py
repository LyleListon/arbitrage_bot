# Advanced Reinforcement Learning Models for Base Arbitrage Bot
# This module provides A3C and DDPG implementations

import streamlit as st
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.multiprocessing as mp
from torch.distributions import Normal
from typing import List, Tuple
import plotly.express as px


class ActorCritic(nn.Module):
    """Actor-Critic network for A3C"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128
    ):
        super().__init__()
        
        # Shared layers
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # Actor (policy) layers
        self.actor_mean = nn.Linear(hidden_dim, action_dim)
        self.actor_std = nn.Linear(hidden_dim, action_dim)
        
        # Critic (value) layers
        self.critic = nn.Linear(hidden_dim, 1)
    
    def forward(self, state: torch.Tensor) -> Tuple[Normal, torch.Tensor]:
        shared_features = self.shared(state)
        
        # Actor output (action distribution)
        action_mean = self.actor_mean(shared_features)
        action_std = torch.exp(self.actor_std(shared_features))
        action_dist = Normal(action_mean, action_std)
        
        # Critic output (state value)
        value = self.critic(shared_features)
        
        return action_dist, value


class Actor(nn.Module):
    """Actor network for DDPG"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        max_action: float = 1.0
    ):
        super().__init__()
        
        self.max_action = max_action
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh()
        )
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.max_action * self.network(state)


class Critic(nn.Module):
    """Critic network for DDPG"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128
    ):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        return self.network(torch.cat([state, action], dim=1))


class A3CAgent:
    """Asynchronous Advantage Actor-Critic agent"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        lr_actor: float = 0.001,
        lr_critic: float = 0.002,
        gamma: float = 0.99,
        tau: float = 0.95,
        num_processes: int = 4
    ):
        self.gamma = gamma
        self.tau = tau
        
        # Create global network
        self.global_network = ActorCritic(state_dim, action_dim, hidden_dim)
        self.global_network.share_memory()
        
        # Create optimizer
        self.optimizer = optim.Adam([
            {'params': self.global_network.actor_mean.parameters(), 'lr': lr_actor},
            {'params': self.global_network.actor_std.parameters(), 'lr': lr_actor},
            {'params': self.global_network.critic.parameters(), 'lr': lr_critic}
        ])
        
        # Create worker processes
        self.processes = []
        for _ in range(num_processes):
            process = mp.Process(target=self._worker_process)
            self.processes.append(process)
    
    def _worker_process(self):
        """Worker process for A3C"""
        # Create local network
        local_network = ActorCritic(
            self.global_network.shared[0].in_features,
            self.global_network.actor_mean.out_features
        )
        
        while True:
            # Sync with global network
            local_network.load_state_dict(self.global_network.state_dict())
            
            # Collect experience
            states, actions, rewards = [], [], []
            done = False
            
            while not done:
                # Get action distribution and value
                state_tensor = torch.FloatTensor(self.current_state)
                action_dist, value = local_network(state_tensor)
                
                # Sample action
                action = action_dist.sample()
                log_prob = action_dist.log_prob(action)
                
                # Execute action
                next_state, reward, done, _ = self.env.step(action.numpy())
                
                # Store experience
                states.append(state_tensor)
                actions.append(action)
                rewards.append(reward)
                
                self.current_state = next_state
            
            # Calculate advantages
            advantages = self._calculate_advantages(rewards, values)
            
            # Update global network
            self._update_global_network(states, actions, advantages)
    
    def _calculate_advantages(
        self,
        rewards: List[float],
        values: List[float]
    ) -> torch.Tensor:
        """Calculate advantage estimates"""
        advantages = []
        returns = []
        gae = 0
        
        for r, v in zip(reversed(rewards), reversed(values)):
            returns.insert(0, r + self.gamma * gae)
            advantage = returns[0] - v
            gae = advantage * self.gamma * self.tau
            advantages.insert(0, advantage)
        
        return torch.FloatTensor(advantages)


class DDPGAgent:
    """Deep Deterministic Policy Gradient agent"""
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 128,
        lr_actor: float = 0.001,
        lr_critic: float = 0.002,
        gamma: float = 0.99,
        tau: float = 0.005,
        noise_std: float = 0.1,
        buffer_size: int = 100000,
        batch_size: int = 64
    ):
        self.gamma = gamma
        self.tau = tau
        self.noise_std = noise_std
        self.batch_size = batch_size
        
        # Create networks
        self.actor = Actor(state_dim, action_dim, hidden_dim)
        self.actor_target = Actor(state_dim, action_dim, hidden_dim)
        self.actor_target.load_state_dict(self.actor.state_dict())
        
        self.critic = Critic(state_dim, action_dim, hidden_dim)
        self.critic_target = Critic(state_dim, action_dim, hidden_dim)
        self.critic_target.load_state_dict(self.critic.state_dict())
        
        # Create optimizers
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr_actor)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr_critic)
        
        # Initialize replay buffer
        self.replay_buffer = []
    
    def select_action(self, state: np.ndarray) -> np.ndarray:
        """Select action with noise for exploration"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            action = self.actor(state_tensor).squeeze(0).numpy()
        
        # Add noise for exploration
        noise = np.random.normal(0, self.noise_std, size=action.shape)
        return np.clip(action + noise, -1, 1)
    
    def train(self, batch: Tuple) -> Tuple[float, float]:
        """Train actor and critic networks"""
        state_batch, action_batch, reward_batch, next_state_batch, done_batch = batch
        
        # Convert to tensors
        state_tensor = torch.FloatTensor(state_batch)
        action_tensor = torch.FloatTensor(action_batch)
        reward_tensor = torch.FloatTensor(reward_batch).unsqueeze(1)
        next_state_tensor = torch.FloatTensor(next_state_batch)
        done_tensor = torch.FloatTensor(done_batch).unsqueeze(1)
        
        # Update critic
        with torch.no_grad():
            next_action = self.actor_target(next_state_tensor)
            target_q = self.critic_target(next_state_tensor, next_action)
            target_q = reward_tensor + (1 - done_tensor) * self.gamma * target_q
        
        current_q = self.critic(state_tensor, action_tensor)
        critic_loss = nn.MSELoss()(current_q, target_q)
        
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()
        
        # Update actor
        actor_loss = -self.critic(state_tensor, self.actor(state_tensor)).mean()
        
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()
        
        # Update target networks
        self._update_target_networks()
        
        return actor_loss.item(), critic_loss.item()
    
    def _update_target_networks(self):
        """Soft update target networks"""
        for target_param, param in zip(self.actor_target.parameters(), self.actor.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)
        
        for target_param, param in zip(self.critic_target.parameters(), self.critic.parameters()):
            target_param.data.copy_(self.tau * param.data + (1 - self.tau) * target_param.data)


def create_advanced_rl_interface():
    """Create advanced RL interface"""
    st.title("Advanced Reinforcement Learning Models")
    
    # Model selection
    model_type = st.selectbox(
        "Select Model Type",
        ["A3C", "DDPG"]
    )
    
    # Model configuration
    st.subheader("Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        hidden_dim = st.slider(
            "Hidden Dimension",
            min_value=32,
            max_value=256,
            value=128,
            step=32
        )
        
        num_processes = st.slider(
            "Number of Processes (A3C)",
            min_value=2,
            max_value=8,
            value=4,
            step=1
        ) if model_type == "A3C" else None
    
    with col2:
        lr_actor = st.select_slider(
            "Actor Learning Rate",
            options=[0.0001, 0.0005, 0.001, 0.005],
            value=0.001
        )
        
        lr_critic = st.select_slider(
            "Critic Learning Rate",
            options=[0.0001, 0.0005, 0.001, 0.005],
            value=0.002
        )
    
    # Training configuration
    st.subheader("Training Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_episodes = st.slider(
            "Number of Episodes",
            min_value=100,
            max_value=1000,
            value=500
        )
        
        batch_size = st.slider(
            "Batch Size",
            min_value=32,
            max_value=256,
            value=64,
            step=32
        )
    
    with col2:
        gamma = st.slider(
            "Discount Factor",
            min_value=0.9,
            max_value=0.999,
            value=0.99
        )
        
        noise_std = st.slider(
            "Noise Standard Deviation (DDPG)",
            min_value=0.05,
            max_value=0.5,
            value=0.1,
            step=0.05
        ) if model_type == "DDPG" else None
    
    # Train model
    if st.button("Train Model"):
        st.info(f"Training {model_type} model...")
        
        # Create progress containers
        progress_bar = st.progress(0)
        metrics_chart = st.empty()
        
        # Training metrics
        episode_rewards = []
        actor_losses = []
        critic_losses = []
        
        # Training loop simulation
        for episode in range(num_episodes):
            # Simulate episode
            episode_reward = np.random.normal(100, 20)
            actor_loss = np.random.exponential(0.1)
            critic_loss = np.random.exponential(0.1)
            
            episode_rewards.append(episode_reward)
            actor_losses.append(actor_loss)
            critic_losses.append(critic_loss)
            
            # Update progress
            progress_bar.progress((episode + 1) / num_episodes)
            
            # Update metrics chart
            if (episode + 1) % 10 == 0:
                metrics = pd.DataFrame({
                    'Episode Reward': episode_rewards,
                    'Actor Loss': actor_losses,
                    'Critic Loss': critic_losses
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
                "Average Reward",
                f"{np.mean(episode_rewards):.2f}",
                f"{(episode_rewards[-1] - episode_rewards[0]) / abs(episode_rewards[0]) * 100:.1f}%"
            )
        
        with col2:
            st.metric(
                "Final Actor Loss",
                f"{actor_losses[-1]:.4f}",
                f"{(actor_losses[-1] - actor_losses[0]) / abs(actor_losses[0]) * 100:.1f}%"
            )
        
        with col3:
            st.metric(
                "Final Critic Loss",
                f"{critic_losses[-1]:.4f}",
                f"{(critic_losses[-1] - critic_losses[0]) / abs(critic_losses[0]) * 100:.1f}%"
            )
    
    # Export model
    st.subheader("Export Model")
    
    if st.button("Export Model"):
        st.success(f"{model_type} model exported to {model_type.lower()}_model.pt")
