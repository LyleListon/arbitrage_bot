from __future__ import annotations
from typing import Dict, Any, Type, Callable, Optional, TypeVar, Union, List
from functools import wraps
import inspect

T = TypeVar('T')

class DependencyContainer:
    """
    Centralized dependency injection and management system
    Provides inversion of control and loose coupling for system components
    """
    
    def __init__(self) -> None:
        self._dependencies: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, key: str, dependency: Any, singleton: bool = False) -> None:
        """
        Register a dependency with optional singleton management
        
        :param key: Unique identifier for the dependency
        :param dependency: Dependency instance or class
        :param singleton: Whether to cache and reuse the dependency
        """
        if singleton:
            self._singletons[key] = None
        self._dependencies[key] = dependency

    def register_factory(self, key: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory method for dynamic dependency creation
        
        :param key: Unique identifier for the dependency
        :param factory: Factory method to create dependency
        """
        self._factories[key] = factory

    def resolve(self, key: str) -> Any:
        """
        Resolve a dependency, supporting singleton and factory patterns
        
        :param key: Dependency identifier
        :return: Resolved dependency instance
        """
        # Check singleton cache first
        if key in self._singletons:
            if self._singletons[key] is None:
                self._singletons[key] = self._create_dependency(key)
            return self._singletons[key]
        
        # Resolve regular dependency
        return self._create_dependency(key)

    def _create_dependency(self, key: str) -> Any:
        """
        Create dependency instance using registered dependency or factory
        
        :param key: Dependency identifier
        :return: Dependency instance
        """
        if key in self._factories:
            return self._factories[key]()
        
        if key in self._dependencies:
            dependency = self._dependencies[key]
            
            # If it's a class, instantiate it intelligently
            if inspect.isclass(dependency):
                # Get constructor signature
                constructor = dependency.__init__
                sig = inspect.signature(constructor)
                
                # Prepare arguments
                kwargs: Dict[str, Any] = {}
                
                # Handle different parameter types
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    
                    # Try to provide default or minimal values
                    if param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    elif param_name == 'input_dim':
                        kwargs[param_name] = 100  # Default input dimension
                    elif param.annotation == int:
                        kwargs[param_name] = 1
                    elif param.annotation == float:
                        kwargs[param_name] = 1.0
                    elif param.annotation == str:
                        kwargs[param_name] = ''
                    elif param.annotation == list:
                        kwargs[param_name] = []
                    elif param.annotation == dict:
                        kwargs[param_name] = {}
                
                # Instantiate with prepared arguments
                try:
                    return dependency(**kwargs)
                except TypeError:
                    # Fallback to no-argument constructor if possible
                    try:
                        return dependency()
                    except TypeError:
                        raise ValueError(f"Cannot instantiate dependency {key}")
            
            return dependency
        
        raise ValueError(f"No dependency registered for key: {key}")

    def inject(self, *dependency_keys: str) -> Callable:
        """
        Decorator for dependency injection
        
        :param dependency_keys: Keys of dependencies to inject
        :return: Decorated function with injected dependencies
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                injected_deps: List[Any] = [self.resolve(key) for key in dependency_keys]
                return func(*args, *injected_deps, **kwargs)
            return wrapper
        return decorator

# Global dependency container
di_container = DependencyContainer()

def configure_dependencies() -> None:
    """
    Initial dependency configuration method
    Sets up core system dependencies
    """
    from dashboard.advanced_arbitrage_detector import AdvancedArbitrageDetector
    from dashboard.trade_executor import TradeExecutor
    from dashboard.blockchain_monitor import BlockchainMonitor
    from dashboard.ml_models import PricePredictor
    from dashboard.advanced_ml import TransformerModel
    
    # Register core dependencies
    di_container.register('arbitrage_detector', AdvancedArbitrageDetector, singleton=True)
    di_container.register('trade_executor', TradeExecutor, singleton=True)
    di_container.register('blockchain_monitor', BlockchainMonitor, singleton=True)
    di_container.register('price_predictor', PricePredictor, singleton=True)

    # Specific factory for TransformerModel with explicit input dimension
    def create_transformer_model() -> TransformerModel:
        return TransformerModel(input_dim=100)
    
    di_container.register_factory('advanced_ml_model', create_transformer_model)

# Utility function for easy dependency retrieval
def get_dependency(key: str) -> Any:
    """
    Retrieve a dependency from the container
    
    :param key: Dependency identifier
    :return: Resolved dependency instance
    """
    return di_container.resolve(key)
