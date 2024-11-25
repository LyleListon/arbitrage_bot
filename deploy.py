#!/usr/bin/env python3
import os
import sys
import subprocess
import platform
import shutil
import venv
import argparse
from typing import Optional, Dict, Any, List, Tuple, Callable

class AutomatedDeployer:
    """
    Automated deployment script for arbitrage trading platform
    Handles environment setup, dependency installation, and configuration
    """
    
    def __init__(self, env_type: str = 'development'):
        """
        Initialize deployment process
        
        :param env_type: Deployment environment type
        """
        self.env_type = env_type
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.venv_path = os.path.join(self.project_root, 'venv')
        self.python_executable = self._find_python_executable()
    
    def _find_python_executable(self) -> str:
        """
        Find the most appropriate Python executable
        
        :return: Path to Python executable
        """
        # Potential Python executable locations
        python_paths = [
            sys.executable,  # Current Python interpreter
            os.path.join(self.venv_path, 'Scripts', 'python.exe') if platform.system() == 'Windows' else '',
            os.path.join(self.venv_path, 'bin', 'python'),
            shutil.which('python3'),
            shutil.which('python'),
            r'C:\Users\listonianapp\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe',
            r'C:\Program Files\Python312\python.exe',
            r'C:\Python312\python.exe',
            '/usr/local/bin/python3',
            '/usr/bin/python3'
        ]
        
        for path in python_paths:
            if path and os.path.exists(path):
                print(f"Using Python executable: {path}")
                return path
        
        raise RuntimeError("No suitable Python executable found")
    
    def _run_command(self, command: str, error_message: str = 'Command failed', use_shell: bool = True) -> bool:
        """
        Execute a shell command
        
        :param command: Command to execute
        :param error_message: Error message if command fails
        :param use_shell: Whether to use shell execution
        :return: Boolean indicating command success
        """
        try:
            result = subprocess.run(
                command, 
                shell=use_shell, 
                check=True, 
                capture_output=True, 
                text=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"{error_message}: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def create_virtual_env(self) -> bool:
        """
        Create a virtual environment
        
        :return: Boolean indicating successful creation
        """
        if os.path.exists(self.venv_path):
            print("Virtual environment already exists.")
            return True
        
        try:
            # Use detected Python executable to create venv
            venv_command = f'{self.python_executable} -m venv {self.venv_path}'
            return self._run_command(venv_command, 'Virtual environment creation failed')
        except Exception as e:
            print(f"Failed to create virtual environment: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """
        Install project dependencies with fallback mechanisms
        
        :return: Boolean indicating successful installation
        """
        requirements_path = os.path.join(self.project_root, 'requirements.txt')
        
        # Upgrade pip first
        pip_upgrade_cmd = f'{self.python_executable} -m pip install --upgrade pip setuptools wheel'
        if not self._run_command(pip_upgrade_cmd, 'Pip upgrade failed'):
            print("Warning: Pip upgrade failed. Continuing with installation...")
        
        # Primary installation attempt
        install_cmd = f'{self.python_executable} -m pip install -r {requirements_path}'
        if self._run_command(install_cmd, 'Dependency installation failed'):
            return True
        
        # Fallback: Try individual package installation
        try:
            with open(requirements_path, 'r') as req_file:
                packages = [
                    line.split('==')[0].strip() 
                    for line in req_file 
                    if line.strip() and not line.startswith('#')
                ]
            
            for package in packages:
                pkg_install_cmd = f'{self.python_executable} -m pip install "{package}"'
                if not self._run_command(pkg_install_cmd, f'Failed to install {package}'):
                    print(f"Warning: Could not install {package}")
            
            return True
        except Exception as e:
            print(f"Fallback installation failed: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """
        Create .env file with placeholder credentials
        
        :return: Boolean indicating successful .env file creation
        """
        env_template_path = os.path.join(self.project_root, '.env.template')
        env_path = os.path.join(self.project_root, '.env')
        
        if os.path.exists(env_path):
            print(".env file already exists.")
            return True
        
        # Create .env.template if it doesn't exist
        if not os.path.exists(env_template_path):
            try:
                with open(env_template_path, 'w') as template:
                    template.write("""# RPC Endpoint API Keys
INFURA_PROJECT_ID=your_infura_project_id
ALCHEMY_API_KEY=your_alchemy_api_key
QUICKNODE_API_KEY=your_quicknode_api_key
""")
                print("Created default .env.template")
            except Exception as e:
                print(f"Failed to create .env.template: {e}")
                return False
        
        try:
            shutil.copy(env_template_path, env_path)
            print(".env file created from template.")
            return True
        except Exception as e:
            print(f"Failed to create .env file: {e}")
            return False
    
    def verify_configuration(self) -> bool:
        """
        Verify RPC endpoint configuration
        
        :return: Boolean indicating successful configuration
        """
        # Use detected Python executable for configuration verification
        verify_cmd = f'{self.python_executable} -c "from configs.performance_optimized_loader import get_rpc_endpoint; print(get_rpc_endpoint(\'ethereum\'))"'
        
        return self._run_command(
            verify_cmd,
            'Configuration verification failed'
        )
    
    def deploy(self) -> bool:
        """
        Automated deployment process
        
        :return: Boolean indicating successful deployment
        """
        print(f"Starting {self.env_type.capitalize()} Deployment")
        
        steps: List[Tuple[Callable[[], bool], str]] = [
            (self.create_virtual_env, "Creating Virtual Environment"),
            (self.install_dependencies, "Installing Dependencies"),
            (self.create_env_file, "Creating Environment Configuration"),
            (self.verify_configuration, "Verifying Configuration")
        ]
        
        overall_success = True
        
        for step, description in steps:
            print(f"\n{description}...")
            if not step():
                print(f"Deployment failed at step: {description}")
                overall_success = False
                break
        
        print("\n🚀 Deployment Successful!" if overall_success else "\n❌ Deployment Failed")
        return overall_success

def main() -> int:
    """
    Main deployment script entry point
    
    :return: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description='Automated Deployment Script')
    parser.add_argument(
        '--env', 
        choices=['development', 'production'], 
        default='development',
        help='Deployment environment type'
    )
    
    args = parser.parse_args()
    
    deployer = AutomatedDeployer(args.env)
    success = deployer.deploy()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
