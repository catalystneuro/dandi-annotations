"""
Main resource service for managing external resources.
"""
import math
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..data.resource_repository import ResourceRepository
from ..domain.models import (
    Resource, ResourceStatus, ResourceSubmissionResult, ResourceApprovalResult,
    ResourceDeletionResult, PaginatedResources, UserResources, DandisetInfo,
    ResourceStatistics
)
from ..domain.exceptions import (
    ResourceNotFoundError, ResourceValidationError, ResourceStateError,
    DandisetNotFoundError, PaginationError
)


class ResourceService:
    """Main service for managing external resources."""
    
    def __init__(self, repository: ResourceRepository):
        """
        Initialize the resource service.
        
        Args:
            repository: The resource repository implementation
        """
        self.repository = repository
    
    def _create_resource_from_data(self, data: Dict[str, Any]) -> Resource:
        """Create a Resource domain object from raw data."""
        resource_id = data.get('_submission_filename', '').replace('.yaml', '')
        dandiset_id = data.get('_dandiset_id', data.get('dandiset_id', ''))
        status_str = data.get('_submission_status', 'community')
        
        # Map status string to enum
        status_map = {
            'community': ResourceStatus.PENDING,
            'approved': ResourceStatus.APPROVED,
            'deleted': ResourceStatus.DELETED
        }
        status = status_map.get(status_str, ResourceStatus.PENDING)
        
        return Resource(
            resource_id=resource_id,
            dandiset_id=dandiset_id,
            status=status,
            data=data
        )
    
    def submit_resource(self, dandiset_id: str, resource_data: Dict[str, Any]) -> ResourceSubmissionResult:
        """
        Submit a new resource for review.
        
        Args:
            dandiset_id: The dandiset identifier
            resource_data: The resource data to submit
            
        Returns:
            ResourceSubmissionResult with submission details
        """
        try:
            # Add submission metadata
            enriched_data = resource_data.copy()
            enriched_data['annotation_date'] = datetime.now().astimezone().isoformat()
            enriched_data['dandiset_id'] = dandiset_id
            
            # Create the resource
            resource_id = self.repository.create_resource(
                dandiset_id, enriched_data, ResourceStatus.PENDING
            )
            
            # Create the resource object
            resource_data_with_meta = self.repository.read_resource(
                dandiset_id, resource_id, ResourceStatus.PENDING
            )
            resource = self._create_resource_from_data(resource_data_with_meta) if resource_data_with_meta else None
            
            return ResourceSubmissionResult(
                success=True,
                resource_id=resource_id,
                message="Resource submitted successfully for review",
                resource=resource
            )
        except Exception as e:
            return ResourceSubmissionResult(
                success=False,
                resource_id=None,
                message=f"Failed to submit resource: {str(e)}",
                errors={'submission_error': str(e)}
            )
    
    def approve_resource(self, dandiset_id: str, resource_id: str, 
                        approver_info: Dict[str, Any]) -> ResourceApprovalResult:
        """
        Approve a pending resource.
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            approver_info: Information about the approver
            
        Returns:
            ResourceApprovalResult with approval details
        """
        try:
            # Check if resource exists in pending status
            resource_data = self.repository.read_resource(
                dandiset_id, resource_id, ResourceStatus.PENDING
            )
            if not resource_data:
                return ResourceApprovalResult(
                    success=False,
                    resource=None,
                    message="Resource not found in pending status",
                    errors={'not_found': 'Resource not found or not pending'}
                )
            
            # Add approval metadata in the format expected by the API
            approval_data = {
                'approval_contributor': {
                    'name': approver_info.get('name', 'Unknown Moderator'),
                    'email': approver_info.get('email', 'unknown'),
                    'schemaKey': 'AnnotationContributor'
                },
                'approval_date': datetime.now().astimezone().isoformat()
            }
            
            # Add optional fields if provided
            if approver_info.get('identifier'):
                approval_data['approval_contributor']['identifier'] = approver_info['identifier']
            if approver_info.get('url'):
                approval_data['approval_contributor']['url'] = approver_info['url']
            
            # Transition from pending to approved
            success = self.repository.transition_resource(
                dandiset_id, resource_id, 
                ResourceStatus.PENDING, ResourceStatus.APPROVED,
                approval_data
            )
            
            if not success:
                return ResourceApprovalResult(
                    success=False,
                    resource=None,
                    message="Failed to approve resource",
                    errors={'transition_error': 'Could not transition resource to approved status'}
                )
            
            # Get the approved resource
            approved_data = self.repository.read_resource(
                dandiset_id, resource_id, ResourceStatus.APPROVED
            )
            resource = self._create_resource_from_data(approved_data) if approved_data else None
            
            return ResourceApprovalResult(
                success=True,
                resource=resource,
                message="Submission approved successfully"
            )
        except Exception as e:
            return ResourceApprovalResult(
                success=False,
                resource=None,
                message=f"Failed to approve resource: {str(e)}",
                errors={'approval_error': str(e)}
            )
    
    def archive_resource(self, dandiset_id: str, resource_id: str, status: ResourceStatus,
                        moderator_info: Dict[str, Any]) -> ResourceDeletionResult:
        """
        Archive a resource (soft delete with backup).
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            status: The current resource status
            moderator_info: Information about the moderator performing the deletion
            
        Returns:
            ResourceDeletionResult with deletion details
        """
        try:
            # Check if resource exists
            resource_data = self.repository.read_resource(dandiset_id, resource_id, status)
            if not resource_data:
                return ResourceDeletionResult(
                    success=False,
                    resource_id=resource_id,
                    message="Resource not found",
                    errors={'not_found': 'Resource not found'}
                )
            
            # Extract resource name for response
            resource_name = resource_data.get('name', f'{resource_id}.yaml')
            
            # Create archive metadata
            archive_metadata = {
                'deleted_by': moderator_info.get('email', 'unknown'),
                'deletion_reason': moderator_info.get('reason', 'No reason provided'),
                'moderator_name': moderator_info.get('name', 'Unknown Moderator')
            }
            
            # Archive the resource
            backup_location = self.repository.archive_resource(
                dandiset_id, resource_id, status, archive_metadata
            )
            
            # Create result with resource name
            result = ResourceDeletionResult(
                success=True,
                resource_id=resource_id,
                message="Resource archived successfully",
                backup_location=backup_location
            )
            # Add resource name as an attribute for the API response
            result.resource_name = resource_name
            return result
        except Exception as e:
            return ResourceDeletionResult(
                success=False,
                resource_id=resource_id,
                message=f"Failed to archive resource: {str(e)}",
                errors={'archive_error': str(e)}
            )
    
    def delete_resource(self, dandiset_id: str, resource_id: str, status: ResourceStatus,
                       moderator_info: Dict[str, Any]) -> ResourceDeletionResult:
        """
        Delete a resource.
        
        Args:
            dandiset_id: The dandiset identifier
            resource_id: The resource identifier
            status: The current resource status
            moderator_info: Information about the moderator performing the deletion
            
        Returns:
            ResourceDeletionResult with deletion details
        """
        return self.archive_resource(dandiset_id, resource_id, status, moderator_info)
    
    def delete_resource_by_id(self, resource_id: str, moderator_info: Dict[str, Any]) -> ResourceDeletionResult:
        """
        Delete a resource by ID (finds it across all dandisets).
        
        Args:
            resource_id: The resource identifier
            moderator_info: Information about the moderator performing the deletion
            
        Returns:
            ResourceDeletionResult with deletion details
        """
        try:
            # Find the resource first
            resource = self.find_resource_by_id(resource_id)
            if not resource:
                return ResourceDeletionResult(
                    success=False,
                    resource_id=resource_id,
                    message="Resource not found",
                    errors={'not_found': 'Resource not found'}
                )
            
            # Extract dandiset_id and status from the resource
            dandiset_id = resource.dandiset_id
            status = resource.status
            
            # Delete the resource
            return self.delete_resource(dandiset_id, resource_id, status, moderator_info)
        except Exception as e:
            return ResourceDeletionResult(
                success=False,
                resource_id=resource_id,
                message=f"Failed to delete resource: {str(e)}",
                errors={'deletion_error': str(e)}
            )
    
    def get_dandiset_resources(self, dandiset_id: str, include_pending: bool = True) -> List[dict]:
        """
        Get all resources for a dandiset.
        
        Args:
            dandiset_id: The dandiset identifier
            include_pending: Whether to include pending resources
            
        Returns:
            List of serialized Resource objects
        """
        try:
            resources = []
            
            # Always get approved resources
            approved_data = self.repository.list_resources(dandiset_id, ResourceStatus.APPROVED)
            for data in approved_data:
                resource = self._create_resource_from_data(data)
                resources.append(resource.serialize())

            # Optionally get pending resources
            if include_pending:
                pending_data = self.repository.list_resources(dandiset_id, ResourceStatus.PENDING)
                for data in pending_data:
                    resource = self._create_resource_from_data(data)
                    resources.append(resource.serialize())

            # Sort by annotation_date (newest first)
            resources.sort(key=lambda r: r['data']['annotation_date'], reverse=True)
            return resources
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get dandiset resources: {str(e)}")

    def get_pending_resources(self, dandiset_id: str) -> List[Resource]:
        """
        Get pending resources for a dandiset.
        
        Args:
            dandiset_id: The dandiset identifier
            
        Returns:
            List of pending serialized Resource objects
        """
        try:
            pending_data = self.repository.list_resources(dandiset_id, ResourceStatus.PENDING)
            resources = []
            for data in pending_data:
                resource = self._create_resource_from_data(data)
                resources.append(resource.serialize())

            return resources
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get pending resources: {str(e)}")
    
    def get_approved_resources(self, dandiset_id: str) -> List[Dict[str, Any]]:
        """
        Get approved resources for a dandiset.
        
        Args:
            dandiset_id: The dandiset identifier
            
        Returns:
            List of approved serialized Resource objects
        """
        try:
            approved_data = self.repository.list_resources(dandiset_id, ResourceStatus.APPROVED)
            resources = []
            for data in approved_data:
                resource = self._create_resource_from_data(data)
                resources.append(resource.serialize())

            return resources
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get approved resources: {str(e)}")
    
    def find_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        """
        Find a resource by ID across all dandisets and statuses.
        
        Args:
            resource_id: The resource identifier
            
        Returns:
            Resource object or None if not found
        """
        try:
            resource_data = self.repository.find_resource_by_id(resource_id)
            if resource_data:
                return self._create_resource_from_data(resource_data)
            return None
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to find resource: {str(e)}")
    
    def get_user_resources(self, user_email: str) -> UserResources:
        """
        Get all resources for a specific user.
        
        Args:
            user_email: The user's email address
            
        Returns:
            UserResources object with user's pending and approved resources
        """
        try:
            pending_data, approved_data = self.repository.get_user_resources(user_email)
            
            pending_resources = []
            for data in pending_data:
                pending_resources.append(self._create_resource_from_data(data))
            
            approved_resources = []
            for data in approved_data:
                approved_resources.append(self._create_resource_from_data(data))
            
            return UserResources(
                user_email=user_email,
                pending_resources=pending_resources,
                approved_resources=approved_resources,
                total_pending=len(pending_resources),
                total_approved=len(approved_resources)
            )
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get user resources: {str(e)}")
    
    def get_paginated_resources(self, dandiset_id: str, status: ResourceStatus, 
                               page: int, per_page: int) -> PaginatedResources:
        """
        Get paginated resources for a dandiset.
        
        Args:
            dandiset_id: The dandiset identifier
            status: The resource status to filter by
            page: Page number (1-based)
            per_page: Number of items per page
            
        Returns:
            PaginatedResources object
        """
        try:
            if page < 1 or per_page < 1:
                raise PaginationError("Page and per_page must be positive integers")
            
            # Get all resources for the dandiset and status
            all_data = self.repository.list_resources(dandiset_id, status)
            total_items = len(all_data)
            total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
            
            # Calculate pagination bounds
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            # Get the page slice
            page_data = all_data[start_idx:end_idx]
            resources = []
            for data in page_data:
                resources.append(self._create_resource_from_data(data))
            
            # Calculate pagination metadata
            has_prev = page > 1
            has_next = page < total_pages
            prev_page = page - 1 if has_prev else None
            next_page = page + 1 if has_next else None
            start_item = start_idx + 1 if total_items > 0 else 0
            end_item = min(end_idx, total_items)
            
            return PaginatedResources(
                resources=resources,
                page=page,
                per_page=per_page,
                total_items=total_items,
                total_pages=total_pages,
                has_prev=has_prev,
                has_next=has_next,
                prev_page=prev_page,
                next_page=next_page,
                start_item=start_item,
                end_item=end_item
            )
        except Exception as e:
            raise PaginationError(f"Failed to get paginated resources: {str(e)}")
    
    def get_resource_statistics(self, dandiset_id: Optional[str] = None) -> ResourceStatistics:
        """
        Get statistics about resources in the system.
        
        Args:
            dandiset_id: Optional dandiset identifier to filter by
            
        Returns:
            ResourceStatistics object
        """
        try:
            if dandiset_id:
                # Statistics for a specific dandiset
                approved_resources = self.repository.list_resources(dandiset_id, ResourceStatus.APPROVED)
                pending_resources = self.repository.list_resources(dandiset_id, ResourceStatus.PENDING)
                
                all_resources = approved_resources + pending_resources
                
                # Count unique contributors
                contributors = set()
                resource_types = {}
                repositories = {}
                
                for resource in all_resources:
                    email = resource.get('annotation_contributor', {}).get('email', '')
                    if email:
                        contributors.add(email)
                    
                    resource_type = resource.get('resourceType', 'Unknown')
                    resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
                    
                    repository = resource.get('repository', 'Unknown')
                    repositories[repository] = repositories.get(repository, 0) + 1
                
                return ResourceStatistics(
                    total_dandisets=1,
                    total_approved_resources=len(approved_resources),
                    total_pending_resources=len(pending_resources),
                    total_resources=len(all_resources),
                    unique_contributors=len(contributors),
                    dandisets_with_resources=1,
                    resource_types=resource_types,
                    repositories=repositories
                )
            else:
                # Global statistics
                all_dandisets = self.repository.list_dandisets_with_resources()
                all_approved = self.repository.list_all_resources(ResourceStatus.APPROVED)
                all_pending = self.repository.list_all_resources(ResourceStatus.PENDING)
                
                all_resources = all_approved + all_pending
                
                # Count unique contributors
                contributors = set()
                resource_types = {}
                repositories = {}
                
                for resource in all_resources:
                    email = resource.get('annotation_contributor', {}).get('email', '')
                    if email:
                        contributors.add(email)
                    
                    resource_type = resource.get('resourceType', 'Unknown')
                    resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
                    
                    repository = resource.get('repository', 'Unknown')
                    repositories[repository] = repositories.get(repository, 0) + 1
                
                return ResourceStatistics(
                    total_dandisets=len(all_dandisets),
                    total_approved_resources=len(all_approved),
                    total_pending_resources=len(all_pending),
                    total_resources=len(all_resources),
                    unique_contributors=len(contributors),
                    dandisets_with_resources=len(all_dandisets),
                    resource_types=resource_types,
                    repositories=repositories
                )
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get resource statistics: {str(e)}")
    
    def get_dandisets_with_resources(self) -> List[dict]:
        """
        Get information about all dandisets that have resources.
        
        Returns:
            List of serialized DandisetInfo objects
        """
        try:
            dandiset_ids = self.repository.list_dandisets_with_resources()
            dandiset_infos = []
            
            for dandiset_id in dandiset_ids:
                pending_count = self.repository.get_resource_count(dandiset_id, ResourceStatus.PENDING)
                approved_count = self.repository.get_resource_count(dandiset_id, ResourceStatus.APPROVED)
                
                # Create display ID (remove dandiset_ prefix)
                display_id = dandiset_id.replace('dandiset_', '') if dandiset_id.startswith('dandiset_') else dandiset_id
                
                dandiset_info = DandisetInfo(
                    dandiset_id=dandiset_id,
                    display_id=display_id,
                    pending_count=pending_count,
                    approved_count=approved_count,
                    total_count=pending_count + approved_count
                )
                dandiset_infos.append(dandiset_info.serialize())

            # Sort by dandiset ID
            dandiset_infos.sort(key=lambda d: d['dandiset_id'])
            return dandiset_infos
        except Exception as e:
            raise ResourceNotFoundError(f"Failed to get dandisets with resources: {str(e)}")
