"""
Domain models for the DANDI annotations system.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


class ResourceStatus(Enum):
    """Status of a resource in the system."""
    PENDING = "community"  # Backward compatibility with existing file structure
    APPROVED = "approved"
    DELETED = "deleted"


@dataclass
class Resource:
    """Domain model for an external resource."""
    resource_id: str
    dandiset_id: str
    status: ResourceStatus
    data: Dict[str, Any]
    
    @property
    def is_approved(self) -> bool:
        """Check if the resource is approved."""
        return self.status == ResourceStatus.APPROVED
    
    @property
    def is_pending(self) -> bool:
        """Check if the resource is pending approval."""
        return self.status == ResourceStatus.PENDING
    
    @property
    def is_deleted(self) -> bool:
        """Check if the resource is deleted."""
        return self.status == ResourceStatus.DELETED
    
    @property
    def name(self) -> str:
        """Get the resource name."""
        return self.data.get('name', 'Unknown Resource')
    
    @property
    def url(self) -> str:
        """Get the resource URL."""
        return self.data.get('url', '')
    
    @property
    def contributor_email(self) -> str:
        """Get the contributor email."""
        return self.data.get('annotation_contributor', {}).get('email', '')


@dataclass
class ResourceSubmissionResult:
    """Result of a resource submission operation."""
    success: bool
    resource_id: Optional[str]
    message: str
    resource: Optional[Resource] = None
    errors: Optional[Dict[str, Any]] = None


@dataclass
class ResourceApprovalResult:
    """Result of a resource approval operation."""
    success: bool
    resource: Optional[Resource]
    message: str
    errors: Optional[Dict[str, Any]] = None


@dataclass
class ResourceDeletionResult:
    """Result of a resource deletion operation."""
    success: bool
    resource_id: Optional[str]
    message: str
    backup_location: Optional[str] = None
    errors: Optional[Dict[str, Any]] = None


@dataclass
class PaginatedResources:
    """Paginated list of resources with metadata."""
    resources: List[Resource]
    page: int
    per_page: int
    total_items: int
    total_pages: int
    has_prev: bool
    has_next: bool
    prev_page: Optional[int]
    next_page: Optional[int]
    start_item: int
    end_item: int


@dataclass
class UserResources:
    """Resources associated with a specific user."""
    user_email: str
    pending_resources: List[Resource]
    approved_resources: List[Resource]
    total_pending: int
    total_approved: int


@dataclass
class DandisetInfo:
    """Information about a dandiset and its resources."""
    dandiset_id: str
    display_id: str
    pending_count: int
    approved_count: int
    total_count: int
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize the dandiset info to a dictionary."""
        return {
            'dandiset_id': self.dandiset_id,
            'display_id': self.display_id,
            'pending_count': self.pending_count,
            'approved_count': self.approved_count,
            'total_count': self.total_count
        }


@dataclass
class ResourceStatistics:
    """Statistics about resources in the system."""
    total_dandisets: int
    total_approved_resources: int
    total_pending_resources: int
    total_resources: int
    unique_contributors: int
    dandisets_with_resources: int
    resource_types: Dict[str, int]
    repositories: Dict[str, int]
