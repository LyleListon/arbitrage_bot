import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    module_name: str = "arbitrage_bot"
) -> logging.Logger:
    """
    Configure logging with consistent formatting and handlers.
    
    Args:
        log_level: The logging level to use
        log_file: Optional specific log file path
        module_name: Name of the module for the logger
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # If no specific log file is provided, use a default based on module name
    if log_file is None:
        log_file = log_dir / f"{module_name}.log"
    
    logger = logging.getLogger(module_name)
    logger.setLevel(log_level)
    
    # Remove any existing handlers
    logger.handlers = []
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(log_level)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger instance with the project's standard configuration.
    
    Args:
        module_name: Name of the module requesting the logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(module_name)
    
    # If the logger doesn't have handlers, set up logging
    if not logger.handlers:
        return setup_logging(module_name=module_name)
    
    return logger
