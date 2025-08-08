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
from typing import Tuple, List, Dict, Any, Optional, Callable
from functools import wraps

from dandiannotations.webapp.repositories.resource_repository import ResourceRepository


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
