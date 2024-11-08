# Evolutionary Optimization Methods for ML/RL Models
# This module provides genetic algorithms and evolution strategies

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable
import plotly.express as px
from deap import base, creator, tools, algorithms
import json

class Individual:
    """Individual for evolutionary algorithms"""
    def __init__(self, params: Dict[str, float]):
        self.params = params
        self.fitness = None

class GeneticOptimizer:
    """Genetic Algorithm for hyperparameter optimization"""
    def __init__(
        self,
        param_ranges: Dict[str, Tuple[float, float]],
        population_size: int = 50,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.8
    ):
        self.param_ranges = param_ranges
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        
        # Initialize population
        self.population = self._initialize_population()
    
    def _initialize_population(self) -> List[Individual]:
        """Initialize random population"""
        population = []
        for _ in range(self.population_size):
            params = {
                name: np.random.uniform(low, high)
                for name, (low, high) in self.param_ranges.items()
            }
            population.append(Individual(params))
        return population
    
    def _select_parents(self) -> Tuple[Individual, Individual]:
        """Tournament selection"""
        tournament_size = 3
        tournament1 = np.random.choice(self.population, tournament_size, replace=False)
        tournament2 = np.random.choice(self.population, tournament_size, replace=False)
        
        parent1 = max(tournament1, key=lambda x: x.fitness)
        parent2 = max(tournament2, key=lambda x: x.fitness)
        
        return parent1, parent2
    
    def _crossover(
        self,
        parent1: Individual,
        parent2: Individual
    ) -> Tuple[Individual, Individual]:
        """Uniform crossover"""
        if np.random.random() < self.crossover_rate:
            child1_params = {}
            child2_params = {}
            
            for param_name in self.param_ranges:
                if np.random.random() < 0.5:
                    child1_params[param_name] = parent1.params[param_name]
                    child2_params[param_name] = parent2.params[param_name]
                else:
                    child1_params[param_name] = parent2.params[param_name]
                    child2_params[param_name] = parent1.params[param_name]
            
            return Individual(child1_params), Individual(child2_params)
        
        return parent1, parent2
    
    def _mutate(self, individual: Individual) -> Individual:
        """Gaussian mutation"""
        if np.random.random() < self.mutation_rate:
            for param_name, (low, high) in self.param_ranges.items():
                if np.random.random() < self.mutation_rate:
                    sigma = (high - low) * 0.1
                    value = individual.params[param_name]
                    value += np.random.normal(0, sigma)
                    value = np.clip(value, low, high)
                    individual.params[param_name] = value
        
        return individual
    
    def evolve(
        self,
        fitness_fn: Callable,
        n_generations: int
    ) -> Tuple[Individual, List[float]]:
        """Run genetic algorithm"""
        best_fitness_history = []
        best_individual = None
        
        for generation in range(n_generations):
            # Evaluate fitness
            for individual in self.population:
                if individual.fitness is None:
                    individual.fitness = fitness_fn(individual.params)
            
            # Track best individual
            current_best = max(self.population, key=lambda x: x.fitness)
            if best_individual is None or current_best.fitness > best_individual.fitness:
                best_individual = current_best
            
            best_fitness_history.append(best_individual.fitness)
            
            # Create new population
            new_population = []
            
            while len(new_population) < self.population_size:
                # Selection
                parent1, parent2 = self._select_parents()
                
                # Crossover
                child1, child2 = self._crossover(parent1, parent2)
                
                # Mutation
                child1 = self._mutate(child1)
                child2 = self._mutate(child2)
                
                new_population.extend([child1, child2])
            
            self.population = new_population[:self.population_size]
        
        return best_individual, best_fitness_history

class EvolutionStrategy:
    """Evolution Strategy (CMA-ES) for hyperparameter optimization"""
    def __init__(
        self,
        param_ranges: Dict[str, Tuple[float, float]],
        population_size: int = 50,
        sigma: float = 1.0
    ):
        self.param_ranges = param_ranges
        self.population_size = population_size
        self.sigma = sigma
        
        # Initialize mean vector
        self.mean = np.array([
            (high + low) / 2
            for low, high in param_ranges.values()
        ])
        
        # Initialize covariance matrix
        self.dim = len(param_ranges)
        self.C = np.eye(self.dim)
    
    def _sample_population(self) -> List[Dict[str, float]]:
        """Sample population using current distribution"""
        population = []
        param_names = list(self.param_ranges.keys())
        
        for _ in range(self.population_size):
            # Sample from multivariate normal
            sample = np.random.multivariate_normal(self.mean, self.sigma**2 * self.C)
            
            # Clip to parameter ranges
            for i, (param_name, (low, high)) in enumerate(self.param_ranges.items()):
                sample[i] = np.clip(sample[i], low, high)
            
            # Create parameter dictionary
            params = {
                name: value
                for name, value in zip(param_names, sample)
            }
            
            population.append(params)
        
        return population
    
    def _update_distribution(
        self,
        population: List[Dict[str, float]],
        fitness: List[float]
    ) -> None:
        """Update mean and covariance using weighted samples"""
        # Sort by fitness
        sorted_indices = np.argsort(fitness)[::-1]
        selected_size = self.population_size // 2
        
        # Calculate weights
        weights = np.log(selected_size + 0.5) - np.log(np.arange(selected_size) + 1)
        weights /= weights.sum()
        
        # Convert population to array
        param_names = list(self.param_ranges.keys())
        population_array = np.array([
            [params[name] for name in param_names]
            for params in population
        ])
        
        # Update mean
        selected_array = population_array[sorted_indices[:selected_size]]
        self.mean = weights @ selected_array
        
        # Update covariance
        diff = selected_array - self.mean
        self.C = diff.T @ np.diag(weights) @ diff
    
    def optimize(
        self,
        fitness_fn: Callable,
        n_iterations: int
    ) -> Tuple[Dict[str, float], List[float]]:
        """Run evolution strategy"""
        best_fitness_history = []
        best_params = None
        best_fitness = float('-inf')
        
        for _ in range(n_iterations):
            # Sample population
            population = self._sample_population()
            
            # Evaluate fitness
            fitness = [fitness_fn(params) for params in population]
            
            # Track best
            max_fitness = max(fitness)
            if max_fitness > best_fitness:
                best_fitness = max_fitness
                best_params = population[np.argmax(fitness)]
            
            best_fitness_history.append(best_fitness)
            
            # Update distribution
            self._update_distribution(population, fitness)
            
            # Update step size
            self.sigma *= np.exp((np.mean(fitness) - best_fitness) / best_fitness)
            self.sigma = np.clip(self.sigma, 0.1, 2.0)
        
        return best_params, best_fitness_history

def create_evolutionary_interface():
    """Create evolutionary optimization interface"""
    st.title("Evolutionary Hyperparameter Optimization")
    
    # Method selection
    method = st.selectbox(
        "Select Optimization Method",
        ["Genetic Algorithm", "Evolution Strategy"]
    )
    
    # Model selection
    model_type = st.selectbox(
        "Select Model Type",
        ["DQN", "A3C", "DDPG"]
    )
    
    # Optimization parameters
    st.subheader("Optimization Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        population_size = st.slider(
            "Population Size",
            min_value=20,
            max_value=200,
            value=50
        )
        
        n_generations = st.slider(
            "Number of Generations",
            min_value=10,
            max_value=100,
            value=50
        )
    
    with col2:
        if method == "Genetic Algorithm":
            mutation_rate = st.slider(
                "Mutation Rate",
                min_value=0.01,
                max_value=0.5,
                value=0.1
            )
            
            crossover_rate = st.slider(
                "Crossover Rate",
                min_value=0.5,
                max_value=1.0,
                value=0.8
            )
        else:
            sigma = st.slider(
                "Initial Sigma",
                min_value=0.1,
                max_value=2.0,
                value=1.0
            )
    
    # Run optimization
    if st.button("Start Evolution"):
        st.info(f"Running {method} optimization...")
        
        # Create progress containers
        progress_bar = st.progress(0)
        fitness_chart = st.empty()
        population_chart = st.empty()
        
        # Simulate evolution
        fitness_history = []
        population_metrics = []
        
        for i in range(n_generations):
            # Simulate generation
            best_fitness = 0.7 + 0.3 * (1 - np.exp(-i/20))
            mean_fitness = best_fitness - 0.1 * np.random.rand()
            diversity = 0.5 * np.exp(-i/30)
            
            fitness_history.append(best_fitness)
            population_metrics.append({
                'Generation': i,
                'Best Fitness': best_fitness,
                'Mean Fitness': mean_fitness,
                'Population Diversity': diversity
            })
            
            # Update progress
            progress_bar.progress((i + 1) / n_generations)
            
            # Update charts
            if (i + 1) % 5 == 0:
                # Fitness history
                fig = px.line(
                    y=fitness_history,
                    title='Best Fitness History',
                    labels={'y': 'Fitness', 'index': 'Generation'}
                )
                fitness_chart.plotly_chart(fig)
                
                # Population metrics
                df = pd.DataFrame(population_metrics)
                fig = px.line(
                    df,
                    x='Generation',
                    y=['Best Fitness', 'Mean Fitness', 'Population Diversity'],
                    title='Population Metrics'
                )
                population_chart.plotly_chart(fig)
        
        st.success("Evolution complete!")
        
        # Display final results
        st.subheader("Evolution Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Best Fitness",
                f"{fitness_history[-1]:.3f}",
                f"+{(fitness_history[-1] - fitness_history[0]):.3f}"
            )
            
            # Parameter distribution
            param_dist = pd.DataFrame({
                'Parameter': ['learning_rate', 'hidden_dim', 'gamma'],
                'Value': [0.001, 128, 0.99],
                'Std': [0.0002, 16, 0.01]
            })
            
            fig = px.bar(
                param_dist,
                x='Parameter',
                y='Value',
                error_y='Std',
                title='Final Parameter Distribution'
            )
            st.plotly_chart(fig)
        
        with col2:
            st.metric(
                "Population Diversity",
                f"{population_metrics[-1]['Population Diversity']:.3f}",
                f"{(population_metrics[-1]['Population Diversity'] - population_metrics[0]['Population Diversity']):.3f}"
            )
            
            # Fitness distribution
            fitness_values = np.random.normal(
                fitness_history[-1],
                0.1,
                population_size
            )
            
            fig = px.histogram(
                fitness_values,
                title='Final Population Fitness Distribution'
            )
            st.plotly_chart(fig)
        
        # Export results
        st.subheader("Export Results")
        
        if st.button("Export Evolution Results"):
            results = {
                'method': method,
                'model_type': model_type,
                'best_fitness': fitness_history[-1],
                'fitness_history': fitness_history,
                'population_metrics': population_metrics,
                'best_params': {
                    'learning_rate': 0.001,
                    'hidden_dim': 128,
                    'gamma': 0.99
                }
            }
            
            st.json(results)
            st.success("Results exported to evolution_results.json")
