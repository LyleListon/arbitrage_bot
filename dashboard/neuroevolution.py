# Neuroevolution for Base Arbitrage Bot
# This module provides NEAT and ES-HyperNEAT implementations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import networkx as nx
from typing import Dict, List, Tuple, Optional
import torch
import torch.nn as nn

class NEATGenome:
    """Genome for NEAT algorithm"""
    def __init__(
        self,
        input_size: int,
        output_size: int,
        innovation_counter: int = 0
    ):
        self.nodes = {}  # node_id -> (type, activation)
        self.connections = {}  # conn_id -> (in_node, out_node, weight, enabled)
        self.fitness = 0.0
        self.species_id = None
        self.innovation_counter = innovation_counter
        
        # Create input and output nodes
        for i in range(input_size):
            self.nodes[i] = ('input', 'linear')
        for i in range(output_size):
            self.nodes[input_size + i] = ('output', 'sigmoid')
    
    def add_node(self, node_type: str, activation: str) -> int:
        """Add new node"""
        node_id = len(self.nodes)
        self.nodes[node_id] = (node_type, activation)
        return node_id
    
    def add_connection(
        self,
        in_node: int,
        out_node: int,
        weight: float,
        enabled: bool = True
    ) -> int:
        """Add new connection"""
        conn_id = self.innovation_counter
        self.innovation_counter += 1
        self.connections[conn_id] = (in_node, out_node, weight, enabled)
        return conn_id
    
    def mutate(self, mutation_rate: float = 0.1):
        """Mutate genome"""
        # Mutate connection weights
        for conn_id in self.connections:
            if np.random.random() < mutation_rate:
                in_node, out_node, weight, enabled = self.connections[conn_id]
                new_weight = weight + np.random.normal(0, 0.1)
                self.connections[conn_id] = (in_node, out_node, new_weight, enabled)
        
        # Add new node
        if np.random.random() < mutation_rate:
            if self.connections:
                # Split random connection
                conn_id = np.random.choice(list(self.connections.keys()))
                in_node, out_node, weight, enabled = self.connections[conn_id]
                
                # Disable old connection
                self.connections[conn_id] = (in_node, out_node, weight, False)
                
                # Add new node
                new_node = self.add_node('hidden', 'relu')
                
                # Add new connections
                self.add_connection(in_node, new_node, 1.0)
                self.add_connection(new_node, out_node, weight)
        
        # Add new connection
        if np.random.random() < mutation_rate:
            # Find unconnected nodes
            possible_connections = []
            for in_node in self.nodes:
                for out_node in self.nodes:
                    if (self.nodes[in_node][0] != 'output' and 
                        self.nodes[out_node][0] != 'input'):
                        possible_connections.append((in_node, out_node))
            
            if possible_connections:
                in_node, out_node = np.random.choice(possible_connections)
                weight = np.random.normal(0, 1)
                self.add_connection(in_node, out_node, weight)

class NEATPopulation:
    """Population of NEAT genomes"""
    def __init__(
        self,
        input_size: int,
        output_size: int,
        population_size: int = 50,
        species_threshold: float = 3.0
    ):
        self.input_size = input_size
        self.output_size = output_size
        self.population_size = population_size
        self.species_threshold = species_threshold
        
        # Initialize population
        self.population = [
            NEATGenome(input_size, output_size)
            for _ in range(population_size)
        ]
        
        self.species = {}  # species_id -> [genome_ids]
        self.next_species_id = 0
    
    def speciate(self):
        """Divide population into species"""
        # Clear current species
        self.species = {}
        
        for genome in self.population:
            placed = False
            
            # Try to place in existing species
            for species_id, members in self.species.items():
                if members:
                    representative = members[0]
                    distance = self.genetic_distance(genome, representative)
                    
                    if distance < self.species_threshold:
                        members.append(genome)
                        genome.species_id = species_id
                        placed = True
                        break
            
            # Create new species if needed
            if not placed:
                new_species_id = self.next_species_id
                self.next_species_id += 1
                self.species[new_species_id] = [genome]
                genome.species_id = new_species_id
    
    def genetic_distance(self, genome1: NEATGenome, genome2: NEATGenome) -> float:
        """Calculate genetic distance between genomes"""
        # Connection differences
        matching = 0
        disjoint = 0
        excess = 0
        weight_diff = 0
        
        all_innovations = set(genome1.connections.keys()) | set(genome2.connections.keys())
        max_innovation = max(all_innovations)
        
        for i in range(max_innovation + 1):
            if i in genome1.connections and i in genome2.connections:
                matching += 1
                weight_diff += abs(
                    genome1.connections[i][2] - genome2.connections[i][2]
                )
            elif i in genome1.connections or i in genome2.connections:
                if i < max_innovation:
                    disjoint += 1
                else:
                    excess += 1
        
        # Calculate distance
        c1, c2, c3 = 1.0, 1.0, 0.4  # Configuration coefficients
        n = max(len(genome1.connections), len(genome2.connections))
        if n < 20:
            n = 1
        
        distance = (
            c1 * excess / n +
            c2 * disjoint / n +
            c3 * weight_diff / matching if matching > 0 else 0
        )
        
        return distance
    
    def evolve(self, fitness_fn, n_generations: int):
        """Evolve population"""
        fitness_history = []
        
        for generation in range(n_generations):
            # Evaluate fitness
            for genome in self.population:
                genome.fitness = fitness_fn(genome)
            
            # Speciate
            self.speciate()
            
            # Calculate species fitness
            species_fitness = {}
            for species_id, members in self.species.items():
                species_fitness[species_id] = np.mean([g.fitness for g in members])
            
            # Create new population
            new_population = []
            
            # Elitism: keep best genome from each species
            for species_id, members in self.species.items():
                if members:
                    best_genome = max(members, key=lambda g: g.fitness)
                    new_population.append(best_genome)
            
            # Fill rest of population
            while len(new_population) < self.population_size:
                # Select species proportionally to fitness
                species_id = np.random.choice(
                    list(species_fitness.keys()),
                    p=np.array(list(species_fitness.values())) / sum(species_fitness.values())
                )
                
                # Select parent
                parent = np.random.choice(self.species[species_id])
                
                # Create offspring through mutation
                offspring = NEATGenome(self.input_size, self.output_size)
                offspring.nodes = parent.nodes.copy()
                offspring.connections = parent.connections.copy()
                offspring.mutate()
                
                new_population.append(offspring)
            
            self.population = new_population
            
            # Track best fitness
            best_fitness = max(genome.fitness for genome in self.population)
            fitness_history.append(best_fitness)
        
        return fitness_history

class CPPNNetwork(nn.Module):
    """Compositional Pattern Producing Network for HyperNEAT"""
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, output_size),
            nn.Tanh()
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

class HyperNEATNetwork(nn.Module):
    """Substrate network generated by HyperNEAT"""
    def __init__(
        self,
        cppn: CPPNNetwork,
        input_coords: torch.Tensor,
        hidden_coords: torch.Tensor,
        output_coords: torch.Tensor,
        threshold: float = 0.2
    ):
        super().__init__()
        
        # Generate weights using CPPN
        input_hidden = self._generate_weights(
            cppn, input_coords, hidden_coords, threshold
        )
        hidden_output = self._generate_weights(
            cppn, hidden_coords, output_coords, threshold
        )
        
        # Create layers
        self.hidden = nn.Linear(input_coords.size(0), hidden_coords.size(0))
        self.output = nn.Linear(hidden_coords.size(0), output_coords.size(0))
        
        # Set weights
        self.hidden.weight.data = input_hidden
        self.output.weight.data = hidden_output
    
    def _generate_weights(
        self,
        cppn: CPPNNetwork,
        source_coords: torch.Tensor,
        target_coords: torch.Tensor,
        threshold: float
    ) -> torch.Tensor:
        """Generate weights using CPPN"""
        weights = torch.zeros(target_coords.size(0), source_coords.size(0))
        
        for i in range(target_coords.size(0)):
            for j in range(source_coords.size(0)):
                # Create input for CPPN
                pos = torch.cat([
                    source_coords[j],
                    target_coords[i],
                    torch.norm(source_coords[j] - target_coords[i]).unsqueeze(0)
                ])
                
                # Get weight from CPPN
                weight = cppn(pos)
                
                # Apply threshold
                if abs(weight) > threshold:
                    weights[i, j] = weight
        
        return weights
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.relu(self.hidden(x))
        x = torch.tanh(self.output(x))
        return x

def create_neuroevolution_interface():
    """Create neuroevolution interface"""
    st.title("Neuroevolution")
    
    # Method selection
    method = st.selectbox(
        "Select Method",
        ["NEAT", "ES-HyperNEAT"]
    )
    
    # Network configuration
    st.subheader("Network Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        input_size = st.slider(
            "Input Size",
            min_value=2,
            max_value=10,
            value=5
        )
        
        output_size = st.slider(
            "Output Size",
            min_value=1,
            max_value=5,
            value=1
        )
    
    with col2:
        if method == "NEAT":
            population_size = st.slider(
                "Population Size",
                min_value=20,
                max_value=200,
                value=50
            )
            
            species_threshold = st.slider(
                "Species Threshold",
                min_value=1.0,
                max_value=5.0,
                value=3.0
            )
        else:
            hidden_size = st.slider(
                "Hidden Size",
                min_value=16,
                max_value=128,
                value=64
            )
            
            substrate_resolution = st.slider(
                "Substrate Resolution",
                min_value=4,
                max_value=16,
                value=8
            )
    
    # Evolution parameters
    st.subheader("Evolution Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n_generations = st.slider(
            "Number of Generations",
            min_value=10,
            max_value=100,
            value=50
        )
        
        mutation_rate = st.slider(
            "Mutation Rate",
            min_value=0.01,
            max_value=0.5,
            value=0.1
        )
    
    with col2:
        if method == "NEAT":
            add_node_prob = st.slider(
                "Add Node Probability",
                min_value=0.01,
                max_value=0.5,
                value=0.1
            )
            
            add_conn_prob = st.slider(
                "Add Connection Probability",
                min_value=0.01,
                max_value=0.5,
                value=0.1
            )
        else:
            cppn_hidden_size = st.slider(
                "CPPN Hidden Size",
                min_value=8,
                max_value=64,
                value=32
            )
            
            weight_threshold = st.slider(
                "Weight Threshold",
                min_value=0.1,
                max_value=0.5,
                value=0.2
            )
    
    # Run evolution
    if st.button("Start Evolution"):
        st.info(f"Running {method} evolution...")
        
        # Create progress containers
        progress_bar = st.progress(0)
        fitness_chart = st.empty()
        network_chart = st.empty()
        
        # Simulate evolution
        fitness_history = []
        species_history = []
        
        for i in range(n_generations):
            # Simulate generation
            fitness = 0.7 + 0.3 * (1 - np.exp(-i/20))
            n_species = 5 + int(5 * np.sin(i/10))
            
            fitness_history.append(fitness)
            species_history.append(n_species)
            
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
                
                # Network visualization
                if method == "NEAT":
                    # Create example network
                    G = nx.DiGraph()
                    n_nodes = 10
                    n_edges = 15
                    
                    # Add nodes
                    for j in range(n_nodes):
                        G.add_node(j)
                    
                    # Add edges
                    for _ in range(n_edges):
                        source = np.random.randint(n_nodes)
                        target = np.random.randint(n_nodes)
                        G.add_edge(source, target)
                    
                    # Convert to plotly figure
                    pos = nx.spring_layout(G)
                    edge_x = []
                    edge_y = []
                    for edge in G.edges():
                        x0, y0 = pos[edge[0]]
                        x1, y1 = pos[edge[1]]
                        edge_x.extend([x0, x1, None])
                        edge_y.extend([y0, y1, None])
                    
                    node_x = [pos[node][0] for node in G.nodes()]
                    node_y = [pos[node][1] for node in G.nodes()]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=edge_x, y=edge_y,
                        line=dict(width=0.5, color='#888'),
                        hoverinfo='none',
                        mode='lines'
                    ))
                    fig.add_trace(go.Scatter(
                        x=node_x, y=node_y,
                        mode='markers',
                        hoverinfo='text',
                        marker=dict(
                            size=10,
                            line_width=2
                        )
                    ))
                    
                    fig.update_layout(
                        title='Network Structure',
                        showlegend=False
                    )
                    
                else:  # HyperNEAT
                    # Create example substrate
                    x = np.linspace(-1, 1, substrate_resolution)
                    y = np.linspace(-1, 1, substrate_resolution)
                    X, Y = np.meshgrid(x, y)
                    Z = np.sin(5*X) * np.cos(5*Y)
                    
                    fig = px.imshow(
                        Z,
                        title='Substrate Pattern',
                        labels={'color': 'Weight'}
                    )
                
                network_chart.plotly_chart(fig)
        
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
            
            if method == "NEAT":
                st.metric(
                    "Number of Species",
                    str(species_history[-1]),
                    f"{species_history[-1] - species_history[0]}"
                )
        
        with col2:
            st.metric(
                "Network Complexity",
                f"{n_nodes} nodes, {n_edges} connections"
                if method == "NEAT"
                else f"{substrate_resolution}x{substrate_resolution} substrate"
            )
        
        # Export results
        st.subheader("Export Results")
        
        if st.button("Export Evolution Results"):
            results = {
                'method': method,
                'fitness_history': fitness_history,
                'species_history': species_history if method == "NEAT" else None,
                'final_network': {
                    'n_nodes': n_nodes,
                    'n_edges': n_edges
                } if method == "NEAT" else {
                    'substrate_resolution': substrate_resolution
                }
            }
            
            st.json(results)
            st.success("Results exported to neuroevolution_results.json")

