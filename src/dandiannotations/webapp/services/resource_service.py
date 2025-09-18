"""
ResourceService: business/service layer for resources/dandisets.

This service implements the higher-level dandiset listing logic (moved
from the previous repository implementation). It uses the repository
for low-level file reads (community/approved submission lists) but
performs aggregation itself.

Pagination is provided as a decorator `paginate` so any list-returning
service method can be wrapped to optionally return a paginated result
when called with `page` and `per_page` keyword arguments.
"""
import math
import re
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional, Callable
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


class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self.repo = repository

    @paginate
    def get_all_dandisets(self) -> List[Dict[str, Any]]:
        """
        Return all dandisets that have submissions (community or approved).

        Each dandiset dict contains:
        - id: directory name (e.g., 'dandiset_000001')
        - display_id: like 'DANDI:000001'
        - community_count
        - approved_count
        - total_count

        When called with kwargs `page` and `per_page` this method will
        return a tuple (paginated_list, pagination_info) due to the
        `@paginate` decorator.
        """
        dandisets = []

        # Iterate through all dandiset directories under the repository base_dir
        for dandiset_dir in self.repo.base_dir.iterdir():
            if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                dandiset_id = dandiset_dir.name

                # Count submissions via repository methods
                community_count = len(self.repo.get_community_submissions(dandiset_id))
                approved_count = len(self.repo.get_approved_submissions(dandiset_id))
                total_count = community_count + approved_count

                # Only include dandisets that have submissions
                if total_count > 0:
                    # Format display name as DANDI:XXXXXX
                    display_id = f"DANDI:{dandiset_id.split('_')[1]}"

                    dandisets.append({
                        'id': dandiset_id,
                        'display_id': display_id,
                        'community_count': community_count,
                        'approved_count': approved_count,
                        'total_count': total_count
                    })

        # Sort by dandiset ID
        dandisets.sort(key=lambda x: x['id'])
        return dandisets

    def get_overview_stats(self, include_community: bool = False) -> Dict[str, Any]:
        """
        Compute overview statistics across all dandisets.

        Args:
            include_community: If True include community submissions in totals;
                               otherwise community totals will be zeroed.

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
        if include_community:
            total_community = sum(ds.get('community_count', 0) for ds in all_dandisets)

            # Compute distinct contributor names across all pending submissions
            contributor_names = set()
            for ds in all_dandisets:
                if ds.get('community_count', 0) > 0:
                    for sub in self.repo.get_community_submissions(ds['id']):
                        name = sub.get('annotation_contributor', {}).get('name')
                        if name:
                            contributor_names.add(name)
            unique_contributors = len(contributor_names)
        else:
            total_community = 0

        return {
            'total_approved': total_approved,
            'total_community': total_community,
            'total_dandisets': total_dandisets,
            'unique_contributors': unique_contributors,
        }

    def submit_resource(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and save a new community submission.
        
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
        
        # Save to community submissions folder using repository
        resource_id = self.repo.save_resource(dandiset_id=form_data['dandiset_id'], external_resource=resource)

        # Return properly formatted response data for API consumption
        return {
            'resource_id': resource_id,
            'status': 'pending',
            'resource': resource_data,
        }

    @paginate
    def get_approved_resources(self, dandiset_id: str) -> List[Dict[str, Any]]:
        """
        Return approved resources for a dandiset.

        When called with kwargs page/per_page, returns (items, pagination_info).
        """
        return self.repo.get_approved_submissions(dandiset_id)

    @paginate
    def get_pending_resources(self, dandiset_id: str) -> List[Dict[str, Any]]:
        """
        Return community (pending) resources for a dandiset.

        When called with kwargs page/per_page, returns (items, pagination_info).
        """
        return self.repo.get_community_submissions(dandiset_id)

    @paginate
    def get_all_approved_resources(self) -> List[Dict[str, Any]]:
        """
        Return all approved resources across all dandisets.

        When called with kwargs page/per_page, returns (items, pagination_info).
        """
        return self.repo.get_all_approved_submissions()

    @paginate
    def get_all_pending_resources(self) -> List[Dict[str, Any]]:
        """
        Return all pending (community) resources across all dandisets.

        When called with kwargs page/per_page, returns (items, pagination_info).
        """
        return self.repo.get_all_community_submissions()

    def get_submission_by_filename(self, dandiset_id: str, filename: str, status: str = "community") -> Optional[Dict[str, Any]]:
        """
        Retrieve a single submission by filename and status via the repository.
        """
        return self.repo.get_submission_by_filename(dandiset_id, filename, status)

    # ---------------------------
    # Validation helpers (service-layer validation)
    # ---------------------------
    def _validate_dandiset_id(self, dandiset_id: str) -> None:
        """
        Validate dandiset ID format: either 6 digits (000001) or 'dandiset_000001'.
        Raises ValueError on invalid input.
        """
        if not dandiset_id:
            raise ValueError("Dandiset ID is required")
        pattern = r'^(dandiset_)?[0-9]{6}$'
        if not re.match(pattern, dandiset_id):
            raise ValueError("Invalid dandiset ID format. Use 6 digits (e.g., 000001) or full format (e.g., dandiset_000001)")

    def _validate_email(self, email: Optional[str]) -> None:
        if not email:
            raise ValueError("Moderator email is required")
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError("Invalid moderator email format")

    def _validate_url(self, url: Optional[str]) -> None:
        if not url:
            return
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(pattern, url):
            raise ValueError("Invalid moderator URL format. Must start with http:// or https://")

    def _validate_orcid(self, orcid: Optional[str]) -> None:
        if not orcid:
            return
        pattern = r'^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
        if not re.match(pattern, orcid):
            raise ValueError("Invalid moderator ORCID format. Should be like: https://orcid.org/0000-0000-0000-0000")

    # ---------------------------
    # Serialization helper (service-layer serialization)
    # ---------------------------
    def _serialize_resource(self, resource: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Normalize a resource dict for API/UI consumption (lightweight serializer).
        - Ensures dandiset_id key exists (from _dandiset_id)
        - Adds id derived from filename if not present
        """
        if not resource:
            return None
        serialized = dict(resource)
        if '_dandiset_id' in serialized and 'dandiset_id' not in serialized:
            serialized['dandiset_id'] = serialized.get('_dandiset_id')
        if '_submission_filename' in serialized and 'id' not in serialized:
            try:
                serialized['id'] = serialized['_submission_filename'].replace('.yaml', '')
            except Exception:
                pass
        return serialized

    # ---------------------------
    # Moderation: GET pending submission (with validation + serialization)
    # ---------------------------
    def get_pending_submission(self, dandiset_id: str, filename: str) -> Optional[Dict[str, Any]]:
        """
        Validate input and return the pending (community) submission, serialized.
        Returns None if not found.
        Raises ValueError on validation failures.
        """
        self._validate_dandiset_id(dandiset_id)
        submission = self.repo.get_submission_by_filename(dandiset_id, filename, "community")
        return self._serialize_resource(submission)

    def approve_submission(self, dandiset_id: str, filename: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate moderator payload, approve the pending submission, and return the approved record (serialized).

        Expected data keys:
          - moderator_name (required)
          - moderator_email (required)
          - moderator_identifier (optional)
          - moderator_url (optional)
        """
        # Validate dandiset_id
        self._validate_dandiset_id(dandiset_id)

        # Extract and validate moderator fields
        name = (data or {}).get('moderator_name', '').strip()
        email = (data or {}).get('moderator_email', '').strip()
        identifier = (data or {}).get('moderator_identifier', '').strip() if data else None
        url_field = (data or {}).get('moderator_url', '').strip() if data else None

        if not name:
            raise ValueError("Moderator name is required")
        self._validate_email(email)
        self._validate_orcid(identifier)
        self._validate_url(url_field)

        moderator_info = {'name': name, 'email': email}
        if identifier:
            moderator_info['identifier'] = identifier
        if url_field:
            moderator_info['url'] = url_field

        # Ensure the pending submission exists before attempting approval
        pending = self.repo.get_submission_by_filename(dandiset_id, filename, "community")
        if not pending:
            # Let the route decide 404 vs 500 by raising FileNotFoundError
            raise FileNotFoundError("Submission not found")

        # Approve via repository
        success = self.repo.approve_submission(dandiset_id, filename, moderator_info)
        if not success:
            raise Exception("Approval failed")

        approved = self.repo.get_submission_by_filename(dandiset_id, filename, "approved")
        return self._serialize_resource(approved)

    def delete_submission(self, dandiset_id: str, filename: str, status: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete a submission (community or approved) and return a deletion summary.

        Args:
            dandiset_id: Dandiset identifier (may be 'dandiset_XXXXXX' or 'XXXXXX')
            filename: Submission filename to delete
            status: 'community' or 'approved'
            data: JSON payload containing moderator info:
                  - moderator_name (required)
                  - moderator_email (required)
                  - moderator_identifier (optional)
                  - moderator_url (optional)

        Returns:
            Dict with deletion summary fields:
              - dandiset_id, filename, status, resource_name, deleted_by, deletion_date (ISO)
        """
        # Basic input checks
        self._validate_dandiset_id(dandiset_id)
        status_norm = (status or '').strip().lower()
        if status_norm not in {'community', 'approved'}:
            raise ValueError("Status parameter must be 'community' or 'approved'")

        name = (data or {}).get('moderator_name', '').strip()
        email = (data or {}).get('moderator_email', '').strip()
        identifier = (data or {}).get('moderator_identifier', '').strip() if data else None
        url_field = (data or {}).get('moderator_url', '').strip() if data else None

        if not name:
            raise ValueError("Moderator name is required")
        self._validate_email(email)
        self._validate_orcid(identifier)
        self._validate_url(url_field)

        moderator_info = {'name': name, 'email': email}
        if identifier:
            moderator_info['identifier'] = identifier
        if url_field:
            moderator_info['url'] = url_field

        # Load submission pre-delete to capture resource_name
        submission = self.repo.get_submission_by_filename(dandiset_id, filename, status_norm)
        if not submission:
            raise FileNotFoundError("Submission not found")

        resource_name = submission.get('name', filename)

        # Delegate deletion to repository (moves to backup and deletes original)
        success = self.repo.delete_submission(dandiset_id, filename, status_norm, moderator_info)
        if not success:
            raise Exception("Deletion failed")

        deletion_date = datetime.now().astimezone().isoformat()
        return {
            'dandiset_id': dandiset_id,
            'filename': filename,
            'status': status_norm,
            'resource_name': resource_name,
            'deleted_by': name,
            'deletion_date': deletion_date,
        }

    def get_user_submissions_paginated(self, user_email: str, community_page: int = 1, approved_page: int = 1, per_page: int = 9) -> Dict[str, Any]:
        """
        Return current user's submissions (community and approved) with pagination metadata.
        """
        community_submissions, community_pagination, approved_submissions, approved_pagination = \
            self.repo.get_user_submissions_paginated(user_email, community_page, approved_page, per_page)

        return {
            'community_submissions': community_submissions,
            'approved_submissions': approved_submissions,
            'community_pagination': community_pagination,
            'approved_pagination': approved_pagination,
        }

    def get_dandiset_stats(self, dandiset_id: str) -> Dict[str, Any]:
        """
        Return detailed statistics for a specific dandiset.
        Computed from approved + community lists to avoid brittle existence checks.
        """
        # Fetch lists using repository helpers (these tolerate missing dirs)
        approved_submissions = self.repo.get_approved_submissions(dandiset_id)
        community_submissions = self.repo.get_community_submissions(dandiset_id)

        # Build display ID
        display_id = f"DANDI:{dandiset_id.split('_')[1]}" if '_' in dandiset_id else f"DANDI:{dandiset_id.zfill(6)}"

        # Aggregate counts
        approved_count = len(approved_submissions)
        pending_count = len(community_submissions)
        total_count = approved_count + pending_count

        # Unique contributors across both lists
        unique_contributors = len({
            sub.get('annotation_contributor', {}).get('name')
            for sub in approved_submissions + community_submissions
            if sub.get('annotation_contributor', {}).get('name')
        })

        # Breakdown counts
        resource_types = {}
        repositories = {}
        for sub in approved_submissions + community_submissions:
            rt = sub.get('resourceType', 'Unknown')
            repo = sub.get('repository', 'Unknown')
            resource_types[rt] = resource_types.get(rt, 0) + 1
            repositories[repo] = repositories.get(repo, 0) + 1

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
