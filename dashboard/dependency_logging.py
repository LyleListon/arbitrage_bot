import logging
import time
import uuid
from typing import Any, Dict, Callable, Optional
from functools import wraps
import inspect
import traceback

class DependencyLogger:
    """
    Advanced logging system for dependency injection
    Provides comprehensive tracing and monitoring of dependency lifecycle
    """

    def __init__(self, log_level: int = logging.INFO) -> None:
        """
        Initialize dependency logging system
        
        :param log_level: Logging verbosity level
        """
        # Configure structured logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('dependency_injection.log')
            ]
        )
        self.logger = logging.getLogger('DependencyInjection')
        
        # Tracing configuration
        self.trace_id_key = 'dependency_trace_id'
        
    def log_dependency_creation(
        self, 
        key: str, 
        dependency_type: type, 
        creation_method: str
    ) -> str:
        """
        Log dependency creation event
        
        :param key: Dependency identifier
        :param dependency_type: Type of dependency
        :param creation_method: How the dependency was created
        :return: Trace ID for the creation event
        """
        trace_id = str(uuid.uuid4())
        self.logger.info(
            f"Dependency Created | "
            f"Key: {key} | "
            f"Type: {dependency_type.__name__} | "
            f"Method: {creation_method} | "
            f"TraceID: {trace_id}"
        )
        return trace_id
    
    def log_dependency_resolution(
        self, 
        key: str, 
        dependency: Any, 
        resolution_time: float
    ) -> None:
        """
        Log dependency resolution event
        
        :param key: Dependency identifier
        :param dependency: Resolved dependency
        :param resolution_time: Time taken to resolve
        """
        self.logger.info(
            f"Dependency Resolved | "
            f"Key: {key} | "
            f"Type: {type(dependency).__name__} | "
            f"Resolution Time: {resolution_time:.4f}s"
        )
    
    def log_dependency_error(
        self, 
        key: str, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log dependency creation or resolution errors
        
        :param key: Dependency identifier
        :param error: Exception that occurred
        :param context: Additional error context
        """
        error_context = context or {}
        self.logger.error(
            f"Dependency Error | "
            f"Key: {key} | "
            f"Error: {type(error).__name__} | "
            f"Message: {str(error)} | "
            f"Context: {error_context} | "
            f"Traceback: {traceback.format_exc()}"
        )
    
    def trace_dependency_method(self) -> Callable:
        """
        Decorator to trace method calls within dependencies
        Adds performance and call tracking
        
        :return: Decorated method
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.time()
                trace_id = str(uuid.uuid4())
                
                try:
                    # Log method entry
                    self.logger.debug(
                        f"Method Entry | "
                        f"Method: {func.__name__} | "
                        f"TraceID: {trace_id}"
                    )
                    
                    # Execute method
                    result = func(*args, **kwargs)
                    
                    # Log method exit
                    execution_time = time.time() - start_time
                    self.logger.debug(
                        f"Method Exit | "
                        f"Method: {func.__name__} | "
                        f"TraceID: {trace_id} | "
                        f"Execution Time: {execution_time:.4f}s"
                    )
                    
                    return result
                
                except Exception as e:
                    # Log method error
                    self.logger.error(
                        f"Method Error | "
                        f"Method: {func.__name__} | "
                        f"TraceID: {trace_id} | "
                        f"Error: {type(e).__name__} | "
                        f"Message: {str(e)}"
                    )
                    raise
            
            return wrapper
        return decorator

# Global dependency logging instance
dependency_logger = DependencyLogger()

def configure_dependency_logging(log_level: int = logging.INFO) -> None:
    """
    Configure global dependency logging settings
    
    :param log_level: Logging verbosity level
    """
    global dependency_logger
    dependency_logger = DependencyLogger(log_level)

# Utility decorators for easy logging
def log_dependency_creation(key: str) -> Callable:
    """
    Decorator to log dependency creation
    
    :param key: Dependency identifier
    :return: Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                dependency = func(*args, **kwargs)
                dependency_logger.log_dependency_creation(
                    key, 
                    type(dependency), 
                    func.__name__
                )
                return dependency
            except Exception as e:
                dependency_logger.log_dependency_error(key, e)
                raise
        return wrapper
    return decorator
