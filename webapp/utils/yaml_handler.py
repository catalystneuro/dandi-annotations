"""
YAML file handling utilities for external resources
"""
import yaml
import os
import shutil
from datetime import datetime
from typing import Dict, Any

class YAMLHandler:
    def __init__(self, yaml_file_path: str):
        self.yaml_file_path = yaml_file_path
        
    def create_backup(self):
        """Create a backup of the YAML file before modification"""
        if os.path.exists(self.yaml_file_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.yaml_file_path}.backup_{timestamp}"
            shutil.copy2(self.yaml_file_path, backup_path)
            return backup_path
        return None
    
    def load_resources(self):
        """Load existing resources from YAML file"""
        if not os.path.exists(self.yaml_file_path):
            return []
        
        try:
            with open(self.yaml_file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                return data if data is not None else []
        except Exception as e:
            raise Exception(f"Error loading YAML file: {str(e)}")
    
    def save_resources(self, resources):
        """Save resources to YAML file"""
        try:
            # Create backup before saving
            self.create_backup()
            
            with open(self.yaml_file_path, 'w', encoding='utf-8') as file:
                yaml.dump(resources, file, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
        except Exception as e:
            raise Exception(f"Error saving YAML file: {str(e)}")
    
    def add_resource(self, resource_data: Dict[str, Any]):
        """Add a new resource to the YAML file"""
        try:
            # Load existing resources
            resources = self.load_resources()
            
            # Add the new resource
            resources.append(resource_data)
            
            # Save back to file
            self.save_resources(resources)
            
            return True
        except Exception as e:
            raise Exception(f"Error adding resource: {str(e)}")
    
    def validate_yaml_structure(self, data):
        """Basic validation of YAML structure"""
        if not isinstance(data, list):
            raise ValueError("YAML file should contain a list of resources")
        
        for item in data:
            if not isinstance(item, dict):
                raise ValueError("Each resource should be a dictionary")
            
            # Check for required fields
            required_fields = ['name', 'url', 'relation', 'resourceType', 'schemaKey']
            for field in required_fields:
                if field not in item:
                    raise ValueError(f"Missing required field: {field}")
        
        return True
