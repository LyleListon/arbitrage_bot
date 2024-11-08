"""
Dashboard initialization script

@CONTEXT: Sets up dashboard environment and validates configuration
@LAST_POINT: 2024-01-31 - Added network-specific initialization
"""

import os
import sys
import logging
import importlib
from pathlib import Path
from typing import Tuple, Optional

try:
    import psutil
except ImportError:
    print("Error: psutil package is required. Install with: pip install psutil")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version() -> bool:
    """Check Python version compatibility"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        logger.error(f"Python {required_version[0]}.{required_version[1]} or higher is required")
        return False
    return True


def setup_directories() -> bool:
    """Create required directories"""
    try:
        dirs = ['logs', 'static', 'data']
        dashboard_dir = Path(__file__).parent
        
        for dir_name in dirs:
            dir_path = dashboard_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False


def check_network_config(network: str) -> Tuple[bool, Optional[str]]:
    """Check network-specific configuration files"""
    try:
        dashboard_dir = Path(__file__).parent
        required_files = {
            f'.env.{network}': None,  # Environment file
            f'config/trading_config.{network}.yaml': None  # Config file
        }
        
        missing_files = []
        for filename, template in required_files.items():
            file_path = dashboard_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
        
        if missing_files:
            return False, f"Missing required files for network '{network}': {', '.join(missing_files)}"
        
        return True, None
    except Exception as e:
        logger.error(f"Error checking network config: {e}")
        return False, str(e)


def validate_network_config(network: str) -> Tuple[bool, Optional[str]]:
    """Validate network-specific configuration"""
    try:
        from dashboard.config.config_loader import ConfigLoader
        
        config_loader = ConfigLoader(network=network)
        if not config_loader.load_config():
            return False, f"Failed to load configuration for network '{network}'"
        
        if not config_loader.validate_config():
            return False, f"Invalid configuration for network '{network}'"
        
        # Validate network settings
        net_config = config_loader.get_network_config()
        if net_config.name != network:
            return False, f"Network mismatch in config: expected '{network}', got '{net_config.name}'"
        
        # Additional network-specific validation
        if network == "mainnet":
            # Extra validation for mainnet
            if not net_config.rpc_url or "${" in net_config.rpc_url:
                return False, "Missing or unresolved mainnet RPC URL"
        elif network == "sepolia":
            # Extra validation for testnet
            if not net_config.rpc_url or "${" in net_config.rpc_url:
                return False, "Missing or unresolved Sepolia RPC URL"
        
        return True, None
    except Exception as e:
        logger.error(f"Error validating network config: {e}")
        return False, str(e)


def check_dependencies() -> Tuple[bool, Optional[str]]:
    """Check required Python packages"""
    try:
        required_packages = {
            'flask': 'Flask',
            'flask_socketio': 'Flask-SocketIO',
            'flask_cors': 'Flask-CORS',
            'web3': 'web3',
            'psutil': 'psutil',
            'yaml': 'PyYAML',
            'gevent': 'gevent',
            'python-dotenv': 'python-dotenv'
        }
        
        missing_packages = []
        for import_name, package_name in required_packages.items():
            try:
                if import_name == 'python-dotenv':
                    from dotenv import load_dotenv  # noqa: F401
                else:
                    importlib.import_module(import_name.replace('-', '_'))
                logger.info(f"Found package: {package_name}")
            except ImportError:
                missing_packages.append(package_name)
                logger.warning(f"Missing package: {package_name}")
        
        if missing_packages:
            return False, f"Missing required packages: {', '.join(missing_packages)}"
        
        return True, None
    except Exception as e:
        logger.error(f"Error checking dependencies: {e}")
        return False, str(e)


def check_running_process() -> bool:
    """Check if dashboard is already running"""
    try:
        pid_file = Path(__file__).parent / 'dashboard.pid'
        if pid_file.exists():
            with open(pid_file) as f:
                old_pid = int(f.read().strip())
            try:
                process = psutil.Process(old_pid)
                # Check if it's a Python process
                if process.name().lower() in ['python', 'python.exe']:
                    # Check if it's our dashboard
                    cmdline = ' '.join(process.cmdline()).lower()
                    if 'dashboard' in cmdline:
                        logger.error(f"Dashboard already running with PID {old_pid}")
                        return False
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process doesn't exist or can't be accessed, remove stale PID file
                pid_file.unlink()
        return True
    except Exception as e:
        logger.error(f"Error checking running process: {e}")
        # Return True to allow startup attempt
        return True


def initialize_dashboard(network: str = "development") -> bool:
    """
    Complete dashboard initialization
    
    Args:
        network: Network to initialize (development/sepolia/mainnet)
    """
    try:
        # Check Python version
        if not check_python_version():
            return False
        
        # Check if already running
        if not check_running_process():
            return False
        
        # Setup directories
        if not setup_directories():
            return False
        
        # Check network config files
        config_ok, config_error = check_network_config(network)
        if not config_ok:
            logger.error(f"Network configuration check failed: {config_error}")
            return False
        
        # Validate network configuration
        valid_ok, valid_error = validate_network_config(network)
        if not valid_ok:
            logger.error(f"Network validation failed: {valid_error}")
            return False
        
        # Check dependencies
        deps_ok, deps_error = check_dependencies()
        if not deps_ok:
            logger.error(f"Dependency check failed: {deps_error}")
            return False
        
        logger.info(f"Dashboard initialization successful for network: {network}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing dashboard: {e}")
        return False


if __name__ == '__main__':
    # Get network from command line argument or environment
    network = os.getenv('NETWORK', 'development')
    if len(sys.argv) > 1:
        network = sys.argv[1]
    
    if initialize_dashboard(network):
        logger.info(f"Dashboard ready to start on network: {network}")
        sys.exit(0)
    else:
        logger.error("Dashboard initialization failed")
        sys.exit(1)
