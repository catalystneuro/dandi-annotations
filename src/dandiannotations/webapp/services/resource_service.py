"""
ResourceService: business/service layer for resources/dandisets.

This service implements the higher-level dandiset listing logic (moved
from the previous repository implementation). It uses the repository
for low-level file reads (pending/approved resource lists) but
performs aggregation itself.

Pagination is provided as a decorator `paginate` so any list-returning
service method can be wrapped to optionally return a paginated result
when called with `page` and `per_page` keyword arguments.
"""
import math
import re
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional, Callable, Union
from functools import wraps
import uuid

from dandiannotations.webapp.repositories.resource_repository import ResourceRepository
from dandiannotations.models.models import ExternalResource, AnnotationContributor


def _paginate_list(items: List[Any], page: int = 1, per_page: int = 10) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Paginate a list of items and return pagination metadata.

    Returns (paginated_items, pagination_info).
    """
    total_items = len(items)
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1

    # Ensure page is within valid range
    page = max(1, min(page, total_pages))

    # Calculate start and end indices
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    # Get paginated items
    paginated_items = items[start_idx:end_idx]

    # Create pagination info
    pagination_info = {
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None,
        'start_item': start_idx + 1 if total_items > 0 else 0,
        'end_item': min(end_idx, total_items)
    }

    return paginated_items, pagination_info


def paginate(func: Callable) -> Callable:
    """
    Decorator that makes a list-returning function optionally paginated.

    Behavior:
    - If called without `page` and `per_page` kwargs: returns the original list.
    - If called with `page` (and optionally `per_page`): returns (paginated_list, pagination_info).

    Usage:
        @paginate
        def get_items(self) -> List[dict]:
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract pagination params if provided
        page = kwargs.pop('page', None)
        per_page = kwargs.pop('per_page', None)

        # Call the original function to get the full list
        items = func(*args, **kwargs)

        # If no pagination requested, return full items
        if page is None and per_page is None:
            return items

        # Use defaults if only one provided
        if page is None:
            page = 1
        if per_page is None:
            per_page = 10

        return _paginate_list(items, page, per_page)

    return wrapper


def _serialize_resources(result: Union[ExternalResource, List[ExternalResource]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Serialize ExternalResource or List[ExternalResource] to dict(s) using model_dump.
    Assumes Pydantic v2 models and valid inputs (no legacy transforms).
    """
    if isinstance(result, list):
        return [obj.model_dump(mode="json", exclude_none=True) for obj in result]
    return result.model_dump(mode="json", exclude_none=True)


def serialize_resources(func: Callable[..., Union[ExternalResource, List[ExternalResource]]]) -> Callable[..., Union[Dict[str, Any], List[Dict[str, Any]]]]:
    """
    Decorator: serialize service-layer results (ExternalResource or list thereof) to dict(s).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return _serialize_resources(func(*args, **kwargs))
    return wrapper


class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self.repo = repository

    # ---------------------------
    # Validation helpers (service-layer validation)
    # ---------------------------
    def _validate_status(self, status: str) -> None:
        """
        Validate resource status.
        """
        if status not in {"pending", "approved"}:
            raise ValueError("Status parameter must be 'pending' or 'approved'")


    # ---------------------------
    # Get high-level stats and listings
    # ---------------------------
    @paginate
    def get_all_dandisets(self) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Return all dandisets that have resources (pending or approved).

        Each dandiset dict contains:
        - id: directory name (e.g., 'dandiset_000001')
        - display_id: like 'DANDI:000001'
        - pending_count
        - approved_count
        - total_count

        When called with kwargs `page` and `per_page` this method will
        return a tuple (paginated_list, pagination_info) due to the
        `@paginate` decorator.
        """
        dandisets = []

        # Iterate through dandiset IDs provided by repository
        for dandiset_id in self.repo.get_all_dandiset_ids():
            # Count resources via repository methods
            pending_count = len(self.repo.get_resources_by_dandiset(dandiset_id, 'pending'))
            approved_count = len(self.repo.get_resources_by_dandiset(dandiset_id, 'approved'))
            total_count = pending_count + approved_count

            # Only include dandisets that have resources
            if total_count > 0:
                # Format display name as DANDI:XXXXXX (dandiset_id is already 6 digits)
                display_id = f"DANDI:{dandiset_id}"

                dandisets.append({
                    'id': dandiset_id,
                    'display_id': display_id,
                    'pending_count': pending_count,
                    'approved_count': approved_count,
                    'total_count': total_count
                })

        # Sort by dandiset ID
        dandisets.sort(key=lambda x: x['id'])
        return dandisets

    def get_overview_stats(self, include_pending: bool = False) -> Dict[str, Any]:
        """
        Compute overview statistics across all dandisets.

        Args:
            include_pending: If True include pending resources in totals;
                             otherwise pending totals will be zeroed.

        Returns:
            Dict with keys:
              - total_approved: int
              - total_community: int
              - total_dandisets: int
              - unique_contributors: int (distinct contributor names across pending when include_community=True)
        """
        # Call get_all_dandisets without pagination to get the aggregated list
        all_dandisets = self.get_all_dandisets()
        total_approved = sum(ds.get('approved_count', 0) for ds in all_dandisets)
        total_dandisets = len(all_dandisets)

        unique_contributors = 0
        if include_pending:
            total_pending = sum(ds.get('pending_count', 0) for ds in all_dandisets)

            # Compute distinct contributor names across all pending resources
            contributor_names = set()
            for ds in all_dandisets:
                if ds.get('pending_count', 0) > 0:
                    for sub in self.repo.get_resources_by_dandiset(ds['id'], 'pending'):
                        try:
                            name = sub.annotation_contributor.name if sub.annotation_contributor else None
                        except Exception:
                            name = None
                        if name:
                            contributor_names.add(name)
            unique_contributors = len(contributor_names)
        else:
            total_pending = 0

        return {
            'total_approved': total_approved,
            'total_pending': total_pending,
            'total_dandisets': total_dandisets,
            'unique_contributors': unique_contributors,
        }

    def get_dandiset_stats(self, dandiset_id: str) -> Dict[str, Any]:
        """
        Return detailed statistics for a specific dandiset.
        Computed from approved + pending lists to avoid brittle existence checks.
        """
        # Fetch lists using repository helpers (these tolerate missing dirs)
        approved_submissions = self.repo.get_resources_by_dandiset(dandiset_id, 'approved')
        pending_submissions = self.repo.get_resources_by_dandiset(dandiset_id, 'pending')

        # Build display ID (dandiset_id is already 6 digits)
        display_id = f"DANDI:{dandiset_id}"

        # Aggregate counts
        approved_count = len(approved_submissions)
        pending_count = len(pending_submissions)
        total_count = approved_count + pending_count

        # Unique contributors across both lists
        unique_contributors = len({
            getattr(sub.annotation_contributor, 'name', None)
            for sub in approved_submissions + pending_submissions
            if getattr(sub, 'annotation_contributor', None) and getattr(sub.annotation_contributor, 'name', None)
        })

        # Breakdown counts
        resource_types = {}
        repositories = {}
        for sub in approved_submissions + pending_submissions:
            resource_type = str(sub.resourceType)
            repository = str(sub.repository)
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
            repositories[repository] = repositories.get(repository, 0) + 1

        return {
            'dandiset_id': dandiset_id,
            'display_id': display_id,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'total_count': total_count,
            'unique_contributors': unique_contributors,
            'resource_types': resource_types,
            'repositories': repositories
        }

    # ---------------------------
    # Get resource by dandiset, user, uuid, or all
    # ---------------------------
    @paginate
    @serialize_resources
    def get_resources_by_dandiset(self, dandiset_id: str, status: str) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Return resources for a dandiset by status ('pending' or 'approved').

        When called with kwargs page/per_page, returns (items, pagination_info).
        """
        self._validate_status(status)
        return self.repo.get_resources_by_dandiset(dandiset_id, status)


    @paginate
    @serialize_resources
    def get_all_resources(self, status: str) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Return all resources across all dandisets for a given status.

        When called with kwargs page/per_page, returns (items, pagination_info).
        """
        self._validate_status(status)
        return self.repo.get_all_resources(status)


    @serialize_resources
    def get_resource_by_uuid(self, dandiset_id: str, resource_uuid: str, status: str) -> Optional[Dict[str, Any]]:
        """
        Validate input and return a resource by UUID and status (serialized).
        """
        self._validate_status(status)
        submission = self.repo.get_resource_by_uuid(dandiset_id, resource_uuid, status)
        return submission

    @paginate
    @serialize_resources
    def get_resources_by_user(self, user_email: str, status: str) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Return resources for a user by status.

        When called with kwargs page/per_page, returns (items, pagination_info).
        """
        self._validate_status(status)
        return self.repo.get_resources_by_user(user_email, status)

    # ---------------------------
    # Submission management (create/approve/delete)
    # ---------------------------
    def submit_resource(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and save a new pending resource submission.
        
        Args:
            form_data: Form data dictionary containing submission fields
            
        Returns:
            Dictionary containing the saved resource data and filename
            
        Raises:
            ValueError: If validation fails (including Pydantic validation errors)
            Exception: If saving fails
        """
        # Create annotation contributor data
        contributor_data = {
            'name': form_data['contributor_name'],
            'email': form_data['contributor_email'],
            'schemaKey': 'AnnotationContributor'
        }
        
        # Add optional contributor fields if provided
        if form_data.get('contributor_identifier'):
            contributor_data['identifier'] = form_data['contributor_identifier']
        
        if form_data.get('contributor_url'):
            contributor_data['url'] = form_data['contributor_url']
        
        # Create external resource data
        resource_data = {
            'uuid': str(uuid.uuid4()),
            'dandiset_id': form_data['dandiset_id'],
            'annotation_date': datetime.now().astimezone().isoformat(),
            'name': form_data['resource_name'],
            'url': form_data['resource_url'],
            'repository': form_data['repository'],
            'relation': form_data['relation'],
            'resourceType': form_data['resource_type'],
            'schemaKey': 'ExternalResource'
        }
        
        # Add optional resource identifier if provided
        if form_data.get('resource_identifier'):
            resource_data['identifier'] = form_data['resource_identifier']
        
        # Validate using Pydantic models - let them handle all format validation
        try:
            contributor = AnnotationContributor(**contributor_data)
            resource_data["annotation_contributor"] = contributor
            resource = ExternalResource(**resource_data)
            resource_data = resource.model_dump(mode='json', exclude_none=True)
        except Exception as e:
            raise ValueError(f'Validation error: {str(e)}')
        
        # Save to pending resources folder using repository
        resource_id = self.repo.save_resource(dandiset_id=form_data['dandiset_id'], external_resource=resource)

        # Return properly formatted response data for API consumption
        return {
            'resource_id': resource_id,
            'status': 'pending',
            'resource': resource_data,
        }
    
    @serialize_resources
    def approve_submission_by_uuid(self, dandiset_id: str, resource_uuid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate moderator payload, approve the pending submission by UUID, and return the approved record (serialized).

        Expected data keys:
          - moderator_name (required)
          - moderator_email (required)
          - moderator_identifier (optional)
          - moderator_url (optional)
        """
        # Extract moderator fields and validate via Pydantic model
        name = (data or {}).get('moderator_name', '').strip()
        email = (data or {}).get('moderator_email', '').strip()
        identifier = (data or {}).get('moderator_identifier', '').strip() if data else None
        url_field = (data or {}).get('moderator_url', '').strip() if data else None

        if not name:
            raise ValueError("Moderator name is required")

        try:
            approver = AnnotationContributor(
                name=name,
                email=email,
                identifier=identifier or None,
                url=url_field or None,
            )
        except Exception as e:
            # Normalize Pydantic validation errors to ValueError for route handling
            raise ValueError(f"Validation error: {str(e)}")

        # Ensure the pending submission exists before attempting approval (will raise if missing)
        self.repo.get_resource_by_uuid(dandiset_id, resource_uuid, "pending")

        # Approve via repository
        success = self.repo.approve_submission(dandiset_id, resource_uuid, approver)
        if not success:
            raise Exception("Approval failed")

        approved = self.repo.get_resource_by_uuid(dandiset_id, resource_uuid, "approved")
        return approved

    def delete_submission_by_uuid(self, dandiset_id: str, resource_uuid: str, status: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a resource (pending or approved) by UUID and return a deletion summary.

        Args:
            dandiset_id: Dandiset identifier (6-digit format, e.g., '000001')
            resource_uuid: Resource UUID to delete
            status: 'pending' or 'approved'
            data: JSON payload containing moderator info:
                  - moderator_name (required)
                  - moderator_email (required)
                  - moderator_identifier (optional)
                  - moderator_url (optional)

        Returns:
            Dict with deletion summary fields:
              - dandiset_id, resource_uuid, status, resource_name, deleted_by, deletion_date (ISO)
        """
        # Basic input checks
        self._validate_status(status)

        name = (data or {}).get('moderator_name', '').strip()
        email = (data or {}).get('moderator_email', '').strip()
        identifier = (data or {}).get('moderator_identifier', '').strip() if data else None
        url_field = (data or {}).get('moderator_url', '').strip() if data else None

        if not name:
            raise ValueError("Moderator name is required")

        try:
            moderator = AnnotationContributor(
                name=name,
                email=email,
                identifier=identifier or None,
                url=url_field or None,
            )
        except Exception as e:
            # Normalize Pydantic validation errors to ValueError for route handling
            raise ValueError(f"Validation error: {str(e)}")

        # Load submission pre-delete to capture resource_name
        submission = self.repo.get_resource_by_uuid(dandiset_id, resource_uuid, status)
        resource_name = getattr(submission, 'name', resource_uuid)

        # Delegate deletion to repository (moves to backup and deletes original)
        success = self.repo.delete_submission(dandiset_id, resource_uuid, status, moderator)
        if not success:
            raise Exception("Deletion failed")

        deletion_date = datetime.now().astimezone().isoformat()
        return {
            'dandiset_id': dandiset_id,
            'resource_uuid': resource_uuid,
            'status': status,
            'resource_name': resource_name,
            'deleted_by': name,
            'deletion_date': deletion_date,
        }
