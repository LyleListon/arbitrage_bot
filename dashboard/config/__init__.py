"""
Configuration package initialization

@CONTEXT: Makes config a proper Python package
@LAST_POINT: 2024-01-31 - Added package initialization
"""

from .config_loader import ConfigLoader, MonitoringConfig

__all__ = [
    'ConfigLoader',
    'MonitoringConfig'
]
