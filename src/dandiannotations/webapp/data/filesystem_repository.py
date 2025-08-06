"""
Filesystem implementation of the resource repository.
"""
import os
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .resource_repository import ResourceRepository
from ..domain.models import ResourceStatus
from ..domain.exceptions import (
    RepositoryIOError, RepositoryCorruptionError, ResourceNotFoundError
)


class FileSystemResourceRepository(ResourceRepository):
    """Filesystem-based implementation of the resource repository."""
    
    def __init__(self, base_dir: str):
        """
        Initialize the filesystem repository.
        
        Args:
            base_dir: Base directory for all resource storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def _get_dandiset_dir(self, dandiset_id: str) -> Path:
        """Get the directory path for a specific dandiset."""
        # Normalize dandiset_id (remove 'dandiset_' prefix if present)
        if dandiset_id.startswith('dandiset_'):
            dandiset_id = dandiset_id[9:]
        
        # Ensure it's formatted as dandiset_XXXXXX
        if not dandiset_id.startswith('dandiset_'):
            dandiset_id = f"dandiset_{dandiset_id.zfill(6)}"
        
        return self.base_dir / dandiset_id
    
    def _get_status_dir(self, dandiset_id: str, status: ResourceStatus) -> Path:
        """Get the directory for a specific status."""
        dandiset_dir = self._get_dandiset_dir(dandiset_id)
        status_dir = dandiset_dir / status.value
        status_dir.mkdir(parents=True, exist_ok=True)
        return status_dir
    
    def _generate_resource_id(self) -> str:
        """Generate a timestamped resource ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_submission"
    
    def _get_resource_path(self, dandiset_id: str, resource_id: str, 
                          status: ResourceStatus) -> Path:
        """Get the full path to a resource file."""
        status_dir = self._get_status_dir(dandiset_id, status)
        return status_dir / f"{resource_id}.yaml"
    
    def _load_yaml_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load and parse a YAML file."""
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                return data if data else None
        except yaml.YAMLError as e:
            raise RepositoryCorruptionError(f"Invalid YAML in {file_path}: {str(e)}")
        except Exception as e:
            raise RepositoryIOError(f"Error reading {file_path}: {str(e)}")
    
    def _save_yaml_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Save data to a YAML file."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
        except Exception as e:
            raise RepositoryIOError(f"Error writing {file_path}: {str(e)}")
    
    def create_resource(self, dandiset_id: str, resource_data: Dict[str, Any], 
                       status: ResourceStatus = ResourceStatus.PENDING) -> str:
        """Create a new resource with the given status."""
        try:
            resource_id = self._generate_resource_id()
            resource_path = self._get_resource_path(dandiset_id, resource_id, status)
            
            # Ensure dandiset_id is in the resource data
            resource_data['dandiset_id'] = dandiset_id
            
            self._save_yaml_file(resource_path, resource_data)
            return resource_id
        except Exception as e:
            raise RepositoryIOError(f"Error creating resource: {str(e)}")
    
    def read_resource(self, dandiset_id: str, resource_id: str, 
                     status: ResourceStatus) -> Optional[Dict[str, Any]]:
        """Read a resource by ID and status."""
        try:
            resource_path = self._get_resource_path(dandiset_id, resource_id, status)
            data = self._load_yaml_file(resource_path)
            
            if data:
                # Add metadata about the resource
                data['_submission_filename'] = f"{resource_id}.yaml"
                data['_submission_status'] = status.value
                data['_dandiset_id'] = dandiset_id
            
            return data
        except Exception as e:
            raise RepositoryIOError(f"Error reading resource: {str(e)}")
    
    def update_resource(self, dandiset_id: str, resource_id: str, 
                       status: ResourceStatus, resource_data: Dict[str, Any]) -> bool:
        """Update an existing resource."""
        try:
            resource_path = self._get_resource_path(dandiset_id, resource_id, status)
            
            if not resource_path.exists():
                return False
            
            # Ensure dandiset_id is in the resource data
            resource_data['dandiset_id'] = dandiset_id
            
            self._save_yaml_file(resource_path, resource_data)
            return True
        except Exception as e:
            raise RepositoryIOError(f"Error updating resource: {str(e)}")
    
    def delete_resource(self, dandiset_id: str, resource_id: str, 
                       status: ResourceStatus) -> bool:
        """Delete a resource (hard delete)."""
        try:
            resource_path = self._get_resource_path(dandiset_id, resource_id, status)
            
            if not resource_path.exists():
                return False
            
            resource_path.unlink()
            return True
        except Exception as e:
            raise RepositoryIOError(f"Error deleting resource: {str(e)}")
    
    def transition_resource(self, dandiset_id: str, resource_id: str,
                          from_status: ResourceStatus, to_status: ResourceStatus,
                          updated_data: Optional[Dict[str, Any]] = None) -> bool:
        """Transition a resource from one status to another."""
        try:
            source_path = self._get_resource_path(dandiset_id, resource_id, from_status)
            dest_path = self._get_resource_path(dandiset_id, resource_id, to_status)
            
            if not source_path.exists():
                return False
            
            if dest_path.exists():
                raise RepositoryIOError(f"Resource already exists in {to_status.value} status")
            
            # Load existing data
            resource_data = self._load_yaml_file(source_path)
            if not resource_data:
                return False
            
            # Apply updates if provided
            if updated_data:
                resource_data.update(updated_data)
            
            # Save to new location
            self._save_yaml_file(dest_path, resource_data)
            
            # Remove from old location
            source_path.unlink()
            
            return True
        except Exception as e:
            raise RepositoryIOError(f"Error transitioning resource: {str(e)}")
    
    def archive_resource(self, dandiset_id: str, resource_id: str, 
                        status: ResourceStatus, archive_metadata: Dict[str, Any]) -> str:
        """Archive a resource (soft delete with metadata)."""
        try:
            source_path = self._get_resource_path(dandiset_id, resource_id, status)
            
            if not source_path.exists():
                raise ResourceNotFoundError(f"Resource {resource_id} not found")
            
            # Create deleted directory structure
            dandiset_dir = self._get_dandiset_dir(dandiset_id)
            deleted_dir = dandiset_dir / "deleted" / status.value
            deleted_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"deleted_{timestamp}_{resource_id}.yaml"
            backup_path = deleted_dir / backup_filename
            
            # Load existing data
            resource_data = self._load_yaml_file(source_path)
            if not resource_data:
                raise RepositoryCorruptionError(f"Resource {resource_id} contains no data")
            
            # Add archive metadata
            resource_data['deletion_info'] = archive_metadata
            resource_data['deletion_info']['original_filename'] = f"{resource_id}.yaml"
            resource_data['deletion_info']['original_status'] = status.value
            resource_data['deletion_info']['deletion_date'] = datetime.now().astimezone().isoformat()
            
            # Save to backup location
            self._save_yaml_file(backup_path, resource_data)
            
            # Remove original
            source_path.unlink()
            
            return str(backup_path)
        except Exception as e:
            raise RepositoryIOError(f"Error archiving resource: {str(e)}")
    
    def list_resources(self, dandiset_id: str, status: ResourceStatus) -> List[Dict[str, Any]]:
        """List all resources for a dandiset with the given status."""
        try:
            status_dir = self._get_status_dir(dandiset_id, status)
            resources = []
            
            for yaml_file in status_dir.glob("*.yaml"):
                try:
                    data = self._load_yaml_file(yaml_file)
                    if data:
                        # Add metadata about the resource
                        data['_submission_filename'] = yaml_file.name
                        data['_submission_status'] = status.value
                        data['_dandiset_id'] = dandiset_id
                        resources.append(data)
                except Exception as e:
                    # Log error but continue processing other files
                    print(f"Error loading {yaml_file}: {e}")
                    continue
            
            # Sort by annotation_date (newest first)
            resources.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return resources
        except Exception as e:
            raise RepositoryIOError(f"Error listing resources: {str(e)}")
    
    def list_all_resources(self, status: ResourceStatus) -> List[Dict[str, Any]]:
        """List all resources across all dandisets with the given status."""
        try:
            all_resources = []
            
            # Iterate through all dandiset directories
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    resources = self.list_resources(dandiset_id, status)
                    
                    # Add dandiset info to each resource
                    for resource in resources:
                        resource['_dandiset_id'] = dandiset_id
                        all_resources.append(resource)
            
            # Sort by annotation_date (newest first)
            all_resources.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return all_resources
        except Exception as e:
            raise RepositoryIOError(f"Error listing all resources: {str(e)}")
    
    def list_dandisets_with_resources(self) -> List[str]:
        """List all dandiset IDs that have resources."""
        try:
            dandisets = []
            
            # Iterate through all dandiset directories
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    
                    # Check if dandiset has any resources
                    has_resources = False
                    for status in [ResourceStatus.PENDING, ResourceStatus.APPROVED]:
                        if self.get_resource_count(dandiset_id, status) > 0:
                            has_resources = True
                            break
                    
                    if has_resources:
                        dandisets.append(dandiset_id)
            
            # Sort by dandiset ID
            dandisets.sort()
            return dandisets
        except Exception as e:
            raise RepositoryIOError(f"Error listing dandisets: {str(e)}")
    
    def find_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Find a resource by ID across all dandisets and statuses."""
        try:
            # Search through all dandisets and statuses
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    
                    # Check all statuses
                    for status in [ResourceStatus.APPROVED, ResourceStatus.PENDING]:
                        resource = self.read_resource(dandiset_id, resource_id, status)
                        if resource:
                            return resource
            
            return None
        except Exception as e:
            raise RepositoryIOError(f"Error finding resource: {str(e)}")
    
    def get_resource_count(self, dandiset_id: str, status: ResourceStatus) -> int:
        """Get the count of resources for a dandiset with the given status."""
        try:
            status_dir = self._get_status_dir(dandiset_id, status)
            return len(list(status_dir.glob("*.yaml")))
        except Exception as e:
            raise RepositoryIOError(f"Error counting resources: {str(e)}")
    
    def get_user_resources(self, user_email: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Get all resources (pending and approved) for a specific user."""
        try:
            pending_resources = []
            approved_resources = []
            
            # Iterate through all dandisets
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    
                    # Get pending resources for this dandiset
                    dandiset_pending = self.list_resources(dandiset_id, ResourceStatus.PENDING)
                    for resource in dandiset_pending:
                        contributor_email = resource.get('annotation_contributor', {}).get('email', '')
                        if contributor_email == user_email:
                            resource['_dandiset_id'] = dandiset_id
                            pending_resources.append(resource)
                    
                    # Get approved resources for this dandiset
                    dandiset_approved = self.list_resources(dandiset_id, ResourceStatus.APPROVED)
                    for resource in dandiset_approved:
                        contributor_email = resource.get('annotation_contributor', {}).get('email', '')
                        if contributor_email == user_email:
                            resource['_dandiset_id'] = dandiset_id
                            approved_resources.append(resource)
            
            # Sort by annotation_date (newest first)
            pending_resources.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            approved_resources.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            
            return pending_resources, approved_resources
        except Exception as e:
            raise RepositoryIOError(f"Error getting user resources: {str(e)}")
