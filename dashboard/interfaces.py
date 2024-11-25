from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class TradeOpportunity:
    """
    Standardized trade opportunity representation
    """
    token_in: str
    token_out: str
    amount: float
    network: str
    estimated_profit: float
    gas_cost: float
    timestamp: float

class BlockchainAdapterInterface(ABC):
    """
    Abstract base class for blockchain interactions
    Provides a standardized interface for multi-chain support
    """
    
    @abstractmethod
    def connect(self, network: str) -> Any:
        """
        Establish connection to specified blockchain network
        
        :param network: Target blockchain network identifier
        :return: Blockchain connection object
        """
        pass
    
    @abstractmethod
    def execute_transaction(self, transaction: Dict) -> Any:
        """
        Execute a blockchain transaction
        
        :param transaction: Transaction details
        :return: Transaction execution result
        """
        pass
    
    @abstractmethod
    def estimate_gas(self, transaction: Dict) -> float:
        """
        Estimate gas cost for a transaction
        
        :param transaction: Transaction details
        :return: Estimated gas cost
        """
        pass

class MLModelInterface(ABC):
    """
    Abstract base class for machine learning models
    Provides a standardized interface for predictive and reinforcement learning
    """
    
    @abstractmethod
    def train(self, training_data: Any) -> Dict[str, Any]:
        """
        Train the machine learning model
        
        :param training_data: Dataset for model training
        :return: Training metrics and model performance
        """
        pass
    
    @abstractmethod
    def predict(self, input_data: Any) -> Any:
        """
        Generate predictions using the trained model
        
        :param input_data: Input data for prediction
        :return: Prediction results
        """
        pass
    
    @abstractmethod
    def evaluate_performance(self) -> Dict[str, float]:
        """
        Evaluate and report model performance metrics
        
        :return: Performance metrics dictionary
        """
        pass

class ArbitrageStrategyInterface(ABC):
    """
    Abstract base class for arbitrage trading strategies
    Provides a standardized interface for opportunity detection and execution
    """
    
    @abstractmethod
    def detect_opportunities(self, market_data: Dict[str, Any]) -> List[TradeOpportunity]:
        """
        Detect potential arbitrage opportunities
        
        :param market_data: Current market state and price information
        :return: List of detected trade opportunities
        """
        pass
    
    @abstractmethod
    def validate_opportunity(self, opportunity: TradeOpportunity) -> bool:
        """
        Validate the viability of a trade opportunity
        
        :param opportunity: Trade opportunity to validate
        :return: Boolean indicating opportunity validity
        """
        pass
    
    @abstractmethod
    def calculate_potential_profit(self, opportunity: TradeOpportunity) -> float:
        """
        Calculate potential profit for a trade opportunity
        
        :param opportunity: Trade opportunity
        :return: Estimated profit
        """
        pass

class RiskManagerInterface(ABC):
    """
    Abstract base class for risk management
    Provides a standardized interface for trade risk assessment
    """
    
    @abstractmethod
    def assess_trade_risk(self, opportunity: TradeOpportunity) -> float:
        """
        Assess the risk associated with a trade opportunity
        
        :param opportunity: Trade opportunity to assess
        :return: Risk score (0-1 range)
        """
        pass
    
    @abstractmethod
    def get_risk_thresholds(self) -> Dict[str, float]:
        """
        Retrieve current risk management thresholds
        
        :return: Dictionary of risk thresholds
        """
        pass
    
    @abstractmethod
    def update_risk_profile(self, new_thresholds: Dict[str, float]) -> None:
        """
        Update risk management thresholds
        
        :param new_thresholds: New risk threshold configuration
        """
        pass

class TradeExecutorInterface(ABC):
    """
    Abstract base class for trade execution
    Provides a standardized interface for executing blockchain trades
    """
    
    @abstractmethod
    def execute_trade(self, opportunity: TradeOpportunity) -> bool:
        """
        Execute a trade opportunity
        
        :param opportunity: Trade opportunity to execute
        :return: Boolean indicating successful trade execution
        """
        pass
    
    @abstractmethod
    def rollback_trade(self, opportunity: TradeOpportunity) -> bool:
        """
        Rollback a trade in case of failure
        
        :param opportunity: Trade opportunity to rollback
        :return: Boolean indicating successful rollback
        """
        pass
    
    @abstractmethod
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve recent trade history
        
        :param limit: Number of recent trades to retrieve
        :return: List of trade history entries
        """
        pass

# Utility type hints for type checking and IDE support
ArbitrageStrategy = ArbitrageStrategyInterface
BlockchainAdapter = BlockchainAdapterInterface
MLModel = MLModelInterface
RiskManager = RiskManagerInterface
TradeExecutor = TradeExecutorInterface
