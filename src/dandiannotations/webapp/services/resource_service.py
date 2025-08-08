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
        """
        # Call get_all_dandisets without pagination to get the aggregated list
        all_dandisets = self.get_all_dandisets()
        total_approved = sum(ds.get('approved_count', 0) for ds in all_dandisets)
        total_dandisets = len(all_dandisets)

        if include_community:
            total_community = sum(ds.get('community_count', 0) for ds in all_dandisets)
        else:
            total_community = 0

        return {
            'total_approved': total_approved,
            'total_community': total_community,
            'total_dandisets': total_dandisets,
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
