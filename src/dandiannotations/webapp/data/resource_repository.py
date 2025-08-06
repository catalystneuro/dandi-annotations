"""
Abstract repository interface for resource data operations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from ..domain.models import ResourceStatus


class ResourceRepository(ABC):
    """Abstract base class for resource data operations."""
    
    @abstractmethod
    def create_resource(self, dandiset_id: str, resource_data: Dict[str, Any], 
                       status: ResourceStatus = ResourceStatus.PENDING) -> str:
        """
        Create a new resource with the given status.
        
        Args:
            dandiset_id: The dandiset identifier
            resource_data: The resource data to store
            status: The initial status of the resource
            
        Returns:
            The unique resource identifier (filename without extension)
        """
        pass
    
    @abstractmethod
    def read_resource(self, dandiset_id: str, resource_id: str, 
                     status: ResourceStatus) -> Optional[Dict[str, Any]]:
        """
        Read a resource by ID and status.
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            status: The resource status
            
        Returns:
            The resource data or None if not found
        """
        pass
    
    @abstractmethod
    def update_resource(self, dandiset_id: str, resource_id: str, 
                       status: ResourceStatus, resource_data: Dict[str, Any]) -> bool:
        """
        Update an existing resource.
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            status: The resource status
            resource_data: The updated resource data
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_resource(self, dandiset_id: str, resource_id: str, 
                       status: ResourceStatus) -> bool:
        """
        Delete a resource (hard delete).
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            status: The resource status
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def transition_resource(self, dandiset_id: str, resource_id: str,
                          from_status: ResourceStatus, to_status: ResourceStatus,
                          updated_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition a resource from one status to another.
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            from_status: The current status
            to_status: The target status
            updated_data: Optional updated data to apply during transition
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def archive_resource(self, dandiset_id: str, resource_id: str, 
                        status: ResourceStatus, archive_metadata: Dict[str, Any]) -> str:
        """
        Archive a resource (soft delete with metadata).
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            status: The current resource status
            archive_metadata: Metadata about the archival operation
            
        Returns:
            The archive location/identifier
        """
        pass
    
    @abstractmethod
    def list_resources(self, dandiset_id: str, status: ResourceStatus) -> List[Dict[str, Any]]:
        """
        List all resources for a dandiset with the given status.
        
        Args:
            dandiset_id: The dandiset identifier
            status: The resource status to filter by
            
        Returns:
            List of resource data dictionaries
        """
        pass
    
    @abstractmethod
    def list_all_resources(self, status: ResourceStatus) -> List[Dict[str, Any]]:
        """
        List all resources across all dandisets with the given status.
        
        Args:
            status: The resource status to filter by
            
        Returns:
            List of resource data dictionaries with dandiset information
        """
        pass
    
    @abstractmethod
    def list_dandisets_with_resources(self) -> List[str]:
        """
        List all dandiset IDs that have resources.
        
        Returns:
            List of dandiset identifiers
        """
        pass
    
    @abstractmethod
    def find_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a resource by ID across all dandisets and statuses.
        
        Args:
            resource_id: The resource identifier
            
        Returns:
            The resource data with metadata or None if not found
        """
        pass
    
    @abstractmethod
    def get_resource_count(self, dandiset_id: str, status: ResourceStatus) -> int:
        """
        Get the count of resources for a dandiset with the given status.
        
        Args:
            dandiset_id: The dandiset identifier
            status: The resource status
            
        Returns:
            The count of resources
        """
        pass
    
    @abstractmethod
    def get_user_resources(self, user_email: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get all resources (pending and approved) for a specific user.
        
        Args:
            user_email: The user's email address
            
        Returns:
            Tuple of (pending_resources, approved_resources)
        """
        pass
