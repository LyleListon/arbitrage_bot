#!/usr/bin/env python3
import os
import json
import shutil
import subprocess
import sys
from typing import Dict, List, Optional

class ProjectUpdater:
    """
    Comprehensive project update and synchronization tool
    """
    
    def __init__(self, project_root: str = '.'):
        """
        Initialize project updater
        
        :param project_root: Root directory of the project
        """
        self.project_root = os.path.abspath(project_root)
        self.config_files = [
            'configs/networks/rpc_endpoints.json',
            'configs/local.template.json',
            'configs/template.json'
        ]
        self.dependency_files = [
            'requirements.txt',
            'setup.py',
            'pyproject.toml'
        ]
        self.documentation_files = [
            'README.md',
            'DEPLOYMENT.md',
            'docs/CONFIGURATION_LOADER_GUIDE.md',
            'docs/ARCHITECTURAL_REVIEW.md'
        ]
    
    def _run_command(self, command: str) -> bool:
        """
        Execute a shell command
        
        :param command: Command to execute
        :return: Boolean indicating command success
        """
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True
            )
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Command failed: {e}")
            print(f"Error output: {e.stderr}")
            return False
    
    def update_config_files(self) -> bool:
        """
        Validate and update configuration files
        
        :return: Boolean indicating successful update
        """
        print("\n🔧 Updating Configuration Files...")
        
        for config_path in self.config_files:
            full_path = os.path.join(self.project_root, config_path)
            
            if not os.path.exists(full_path):
                print(f"Warning: Config file not found - {config_path}")
                continue
            
            try:
                with open(full_path, 'r') as config_file:
                    config_data = json.load(config_file)
                
                # Add version information
                config_data['version'] = '1.0.0'
                config_data['last_updated'] = subprocess.check_output(['date']).decode().strip()
                
                with open(full_path, 'w') as config_file:
                    json.dump(config_data, config_file, indent=2)
                
                print(f"✅ Updated {config_path}")
            except Exception as e:
                print(f"❌ Error updating {config_path}: {e}")
                return False
        
        return True
    
    def update_dependencies(self) -> bool:
        """
        Update dependency files
        
        :return: Boolean indicating successful update
        """
        print("\n📦 Updating Dependency Files...")
        
        try:
            # Update requirements.txt
            requirements_path = os.path.join(self.project_root, 'requirements.txt')
            with open(requirements_path, 'w') as req_file:
                req_file.write("""
# Core Dependencies
python-dotenv>=0.19.0
typing-extensions>=4.0.0

# Configuration Management
pydantic>=1.8.0

# Optional Performance Optimization
uvloop>=0.16.0
""")
            print("✅ Updated requirements.txt")
            
            # Upgrade dependencies
            return self._run_command('pip install --upgrade -r requirements.txt')
        
        except Exception as e:
            print(f"❌ Dependency update failed: {e}")
            return False
    
    def update_documentation(self) -> bool:
        """
        Update documentation files
        
        :return: Boolean indicating successful update
        """
        print("\n📄 Updating Documentation...")
        
        for doc_path in self.documentation_files:
            full_path = os.path.join(self.project_root, doc_path)
            
            if not os.path.exists(full_path):
                print(f"Warning: Documentation file not found - {doc_path}")
                continue
            
            try:
                with open(full_path, 'r') as doc_file:
                    content = doc_file.read()
                
                # Update last updated timestamp
                updated_content = content.replace(
                    '<!-- LAST_UPDATED -->',
                    f'<!-- LAST_UPDATED: {subprocess.check_output(["date"]).decode().strip()} -->'
                )
                
                with open(full_path, 'w') as doc_file:
                    doc_file.write(updated_content)
                
                print(f"✅ Updated {doc_path}")
            except Exception as e:
                print(f"❌ Error updating {doc_path}: {e}")
                return False
        
        return True
    
    def run_type_checking(self) -> bool:
        """
        Run type checking with mypy
        
        :return: Boolean indicating type checking success
        """
        print("\n🔍 Running Type Checking...")
        return self._run_command('mypy configs/')
    
    def update_project(self) -> bool:
        """
        Comprehensive project update
        
        :return: Boolean indicating overall update success
        """
        steps = [
            (self.update_config_files, "Configuration Files"),
            (self.update_dependencies, "Dependencies"),
            (self.update_documentation, "Documentation"),
            (self.run_type_checking, "Type Checking")
        ]
        
        overall_success = True
        
        for step, description in steps:
            print(f"\n🚀 Updating {description}...")
            if not step():
                print(f"❌ {description} update failed")
                overall_success = False
        
        return overall_success

def main() -> int:
    """
    Main entry point for project update script
    
    :return: Exit code (0 for success, 1 for failure)
    """
    updater = ProjectUpdater()
    success = updater.update_project()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
