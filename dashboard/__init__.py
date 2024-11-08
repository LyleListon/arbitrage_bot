"""
Dashboard package initialization

@CONTEXT: Makes dashboard a proper Python package
@LAST_POINT: 2024-01-31 - Added package initialization
"""

from .enhanced_app import main as run_dashboard
from .monitoring import monitor, init_monitoring
from .config import ConfigLoader, MonitoringConfig
from .data_providers import (
    BaseDataProvider,
    LiveDataProvider,
    PairConfig,
    ExchangeConfig
)

__version__ = '1.0.0'

__all__ = [
    'run_dashboard',
    'monitor',
    'init_monitoring',
    'ConfigLoader',
    'MonitoringConfig',
    'BaseDataProvider',
    'LiveDataProvider',
    'PairConfig',
    'ExchangeConfig'
]
