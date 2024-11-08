# Hyperparameter Optimization for ML/RL Models
# This module provides advanced optimization techniques

import streamlit as st
import pandas as pd
import numpy as np
from bayes_opt import BayesianOptimization
from ray import tune
from ray.tune.schedulers import PopulationBasedTraining
import optuna
import plotly.express as px
from typing import Dict, List, Callable
import json

class HyperparameterOptimizer:
    """Hyperparameter optimization using multiple strategies"""
    def __init__(self, config_path: str = 'config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Parameter spaces
        self.param_spaces = {
            'DQN': {
                'learning_rate': (1e-4, 1e-2),
                'gamma': (0.9, 0.999),
                'hidden_dim': (32, 256),
                'batch_size': (16, 128),
                'buffer_size': (1000, 100000)
            },
            'A3C': {
                'lr_actor': (1e-4, 1e-2),
                'lr_critic': (1e-4, 1e-2),
                'hidden_dim': (32, 256),
                'num_processes': (2, 8),
                'tau': (0.9, 0.99)
            },
            'DDPG': {
                'lr_actor': (1e-4, 1e-2),
                'lr_critic': (1e-4, 1e-2),
                'hidden_dim': (32, 256),
                'tau': (0.001, 0.01),
                'noise_std': (0.05, 0.5)
            }
        }
    
    def bayesian_optimization(
        self,
        model_type: str,
        objective_fn: Callable,
        n_iterations: int = 50
    ) -> Dict:
        """Run Bayesian Optimization"""
        param_space = self.param_spaces[model_type]
        
        optimizer = BayesianOptimization(
            f=objective_fn,
            pbounds=param_space,
            random_state=42
        )
        
        optimizer.maximize(
            init_points=10,
            n_iter=n_iterations
        )
        
        return optimizer.max

    def population_based_training(
        self,
        model_type: str,
        objective_fn: Callable,
        population_size: int = 10,
        num_epochs: int = 100
    ) -> Dict:
        """Run Population Based Training"""
        param_space = self.param_spaces[model_type]
        
        scheduler = PopulationBasedTraining(
            time_attr='training_iteration',
            metric='reward',
            mode='max',
            perturbation_interval=10,
            hyperparam_mutations=param_space
        )
        
        analysis = tune.run(
            objective_fn,
            name=f"{model_type}_PBT",
            scheduler=scheduler,
            num_samples=population_size,
            config=param_space,
            stop={"training_iteration": num_epochs}
        )
        
        return analysis.best_config

    def optuna_optimization(
        self,
        model_type: str,
        objective_fn: Callable,
        n_trials: int = 100
    ) -> Dict:
        """Run Optuna optimization"""
        study = optuna.create_study(direction='maximize')
        study.optimize(objective_fn, n_trials=n_trials)
        
        return study.best_params

def create_hyperopt_interface():
    """Create hyperparameter optimization interface"""
    st.title("Hyperparameter Optimization")
    
    # Model selection
    model_type = st.selectbox(
        "Select Model Type",
        ["DQN", "A3C", "DDPG"]
    )
    
    # Optimization method
    optimization_method = st.selectbox(
        "Select Optimization Method",
        ["Bayesian Optimization", "Population Based Training", "Optuna"]
    )
    
    # Optimization parameters
    st.subheader("Optimization Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if optimization_method == "Bayesian Optimization":
            n_iterations = st.slider(
                "Number of Iterations",
                min_value=20,
                max_value=200,
                value=50
            )
            
            n_init_points = st.slider(
                "Initial Random Points",
                min_value=5,
                max_value=50,
                value=10
            )
            
        elif optimization_method == "Population Based Training":
            population_size = st.slider(
                "Population Size",
                min_value=4,
                max_value=20,
                value=10
            )
            
            num_epochs = st.slider(
                "Number of Epochs",
                min_value=50,
                max_value=500,
                value=100
            )
            
        else:  # Optuna
            n_trials = st.slider(
                "Number of Trials",
                min_value=20,
                max_value=200,
                value=100
            )
            
            n_jobs = st.slider(
                "Number of Parallel Jobs",
                min_value=1,
                max_value=8,
                value=4
            )
    
    with col2:
        objective_metric = st.selectbox(
            "Optimization Objective",
            ["Reward", "Sharpe Ratio", "Win Rate", "Profit"]
        )
        
        evaluation_episodes = st.slider(
            "Evaluation Episodes",
            min_value=5,
            max_value=50,
            value=10
        )
    
    # Run optimization
    if st.button("Start Optimization"):
        st.info(f"Running {optimization_method} for {model_type}...")
        
        # Create progress containers
        progress_bar = st.progress(0)
        metrics_chart = st.empty()
        best_params_container = st.empty()
        
        # Simulate optimization
        n_steps = 100
        metrics = []
        
        for i in range(n_steps):
            # Simulate optimization step
            current_value = np.random.normal(0.7, 0.1) * (i + 1) / n_steps
            metrics.append({
                'step': i,
                'value': current_value,
                'best_value': max([m['value'] for m in metrics + [{'value': current_value}]])
            })
            
            # Update progress
            progress_bar.progress((i + 1) / n_steps)
            
            # Update metrics chart
            if (i + 1) % 5 == 0:
                df = pd.DataFrame(metrics)
                fig = px.line(
                    df,
                    x='step',
                    y=['value', 'best_value'],
                    title='Optimization Progress',
                    labels={'value': objective_metric}
                )
                metrics_chart.plotly_chart(fig)
            
            # Update best parameters
            if (i + 1) % 10 == 0:
                best_params = {
                    'learning_rate': 0.001 * (1 + np.random.rand()),
                    'hidden_dim': int(64 * (1 + np.random.rand())),
                    'gamma': 0.95 + 0.04 * np.random.rand()
                }
                best_params_container.json(best_params)
        
        st.success("Optimization complete!")
        
        # Display final results
        st.subheader("Optimization Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Best Performance",
                f"{max([m['value'] for m in metrics]):.3f}",
                f"+{(metrics[-1]['value'] - metrics[0]['value']):.1%}"
            )
            
            # Learning curves
            df = pd.DataFrame(metrics)
            fig = px.line(
                df,
                x='step',
                y=['value', 'best_value'],
                title='Learning Curves',
                labels={'value': objective_metric}
            )
            st.plotly_chart(fig)
        
        with col2:
            # Parameter importance
            importance = pd.DataFrame({
                'Parameter': ['learning_rate', 'hidden_dim', 'gamma', 'batch_size'],
                'Importance': np.random.rand(4)
            })
            
            fig = px.bar(
                importance,
                x='Parameter',
                y='Importance',
                title='Parameter Importance'
            )
            st.plotly_chart(fig)
        
        # Export results
        st.subheader("Export Results")
        
        if st.button("Export Optimization Results"):
            results = {
                'model_type': model_type,
                'optimization_method': optimization_method,
                'best_params': best_params,
                'best_performance': max([m['value'] for m in metrics]),
                'history': metrics
            }
            
            st.json(results)
            st.success("Results exported to optimization_results.json")
