"""
ResourceService: business/service layer for resources/dandisets.

This service implements the higher-level dandiset listing logic (moved
from the previous repository implementation). It uses the repository
for low-level file reads (community/approved submission lists) but
performs aggregation and pagination itself.

Public methods:
- get_all_dandisets()
- get_all_dandisets_paginated(page, per_page)
"""
import math
from typing import Tuple, List, Dict, Any, Optional

from dandiannotations.webapp.repositories.resource_repository import ResourceRepository


class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self.repo = repository

    def get_all_dandisets(self) -> List[Dict[str, Any]]:
        """
        Return all dandisets that have submissions (community or approved).

        Each dandiset dict contains:
        - id: directory name (e.g., 'dandiset_000001')
        - display_id: like 'DANDI:000001'
        - community_count
        - approved_count
        - total_count
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

    def _paginate_list(self, items: List[Any], page: int = 1, per_page: int = 10) -> Tuple[List[Any], Dict[str, Any]]:
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

    def get_all_dandisets_paginated(self, page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Return paginated dandisets that have submissions.

        This method uses get_all_dandisets() and paginates the result.
        """
        all_dandisets = self.get_all_dandisets()
        return self._paginate_list(all_dandisets, page, per_page)
