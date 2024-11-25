import os
import sys
import logging
from typing import Dict, Any, Optional, Union, List, cast, Type, TypeVar

# Ensure project root is in Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Type variable for YAML library
YAMLLibrary = TypeVar('YAMLLibrary')

def import_yaml() -> Optional[Type[YAMLLibrary]]:
    """
    Attempt to import YAML library with multiple strategies
    
    :return: Imported YAML library type or None
    """
    yaml_libraries = [
        'yaml',  # PyYAML
        'ruamel.yaml',  # Ruamel YAML
    ]
    
    for library_name in yaml_libraries:
        try:
            return __import__(library_name)  # type: ignore
        except ImportError:
            logging.warning(f"Could not import {library_name}")
    
    logging.error("No YAML library available. Please install PyYAML or ruamel.yaml")
    return None

# Import YAML library
yaml = import_yaml()

class ConfigLoader:
    """
    Robust configuration loader with multiple import strategies
    """
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """
        Load configuration with robust error handling
        
        :param config_path: Path to configuration file
        :return: Loaded configuration or empty dictionary
        """
        if yaml is None:
            logging.error("Cannot load configuration: No YAML library available")
            return {}
        
        try:
            with open(config_path, 'r') as config_file:
                config: Dict[str, Any] = yaml.safe_load(config_file) or {}  # type: ignore
            return config
        except Exception as e:
            logging.error(f"Error loading configuration from {config_path}: {e}")
            return {}

class MonitoringConfig:
    """
    Specific configuration for monitoring system
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        Initialize monitoring configuration
        
        :param config_path: Path to configuration file
        """
        # Attempt to find config file relative to project root
        if not os.path.isabs(config_path):
            config_path = os.path.join(project_root, config_path)
        
        self.config: Dict[str, Any] = ConfigLoader.load_config(config_path)
    
    def get_networks(self) -> List[str]:
        """
        Retrieve monitored networks
        
        :return: List of networks to monitor
        """
        networks = self.config.get('networks')
        if not isinstance(networks, list):
            return ['ethereum', 'binance_smart_chain']
        return [str(network) for network in networks]
    
    def get_monitoring_interval(self) -> int:
        """
        Get monitoring interval
        
        :return: Monitoring interval in seconds
        """
        interval = self.config.get('monitoring_interval')
        if not isinstance(interval, (int, float)):
            return 60
        return int(interval)

# Diagnostic logging
if __name__ == '__main__':
    print(f"Project Root: {project_root}")
    print(f"Python Path: {sys.path}")
    print(f"YAML Library: {yaml}")
