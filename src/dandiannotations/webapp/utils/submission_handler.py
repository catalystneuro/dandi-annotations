"""
Submission handling utilities for the two-tiered external resources system
"""
import os
import yaml
import shutil
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

class SubmissionHandler:
    def __init__(self, base_submissions_dir: str):
        """
        Initialize the submission handler
        
        Args:
            base_submissions_dir: Base directory for all submissions (e.g., 'submissions/')
        """
        self.base_dir = Path(base_submissions_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def _get_dandiset_dir(self, dandiset_id: str) -> Path:
        """Get the directory path for a specific dandiset"""
        # Normalize dandiset_id (remove 'dandiset_' prefix if present)
        if dandiset_id.startswith('dandiset_'):
            dandiset_id = dandiset_id[9:]
        
        # Ensure it's formatted as dandiset_XXXXXX
        if not dandiset_id.startswith('dandiset_'):
            dandiset_id = f"dandiset_{dandiset_id.zfill(6)}"
        
        return self.base_dir / dandiset_id
    
    def _get_community_dir(self, dandiset_id: str) -> Path:
        """Get the community submissions directory for a dandiset"""
        dandiset_dir = self._get_dandiset_dir(dandiset_id)
        community_dir = dandiset_dir / "community"
        community_dir.mkdir(parents=True, exist_ok=True)
        return community_dir
    
    def _get_approved_dir(self, dandiset_id: str) -> Path:
        """Get the approved submissions directory for a dandiset"""
        dandiset_dir = self._get_dandiset_dir(dandiset_id)
        approved_dir = dandiset_dir / "approved"
        approved_dir.mkdir(parents=True, exist_ok=True)
        return approved_dir
    
    def _generate_submission_filename(self) -> str:
        """Generate a timestamped filename for a new submission"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_submission.yaml"
    
    def save_community_submission(self, dandiset_id: str, resource_data: Dict[str, Any]) -> str:
        """
        Save a new community submission
        
        Args:
            dandiset_id: The dandiset identifier
            resource_data: The resource data to save
            
        Returns:
            The filename of the saved submission
        """
        try:
            community_dir = self._get_community_dir(dandiset_id)
            filename = self._generate_submission_filename()
            filepath = community_dir / filename
            
            # Ensure dandiset_id is in the resource data
            resource_data['dandiset_id'] = dandiset_id
            
            with open(filepath, 'w', encoding='utf-8') as file:
                yaml.dump(resource_data, file, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
            
            return filename
        except Exception as e:
            raise Exception(f"Error saving community submission: {str(e)}")
    
    def get_community_submissions(self, dandiset_id: str) -> List[Dict[str, Any]]:
        """
        Get all community submissions for a dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            
        Returns:
            List of community submission data with metadata
        """
        try:
            community_dir = self._get_community_dir(dandiset_id)
            submissions = []
            
            for yaml_file in community_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as file:
                        data = yaml.safe_load(file)
                        if data:
                            # Add metadata about the submission
                            data['_submission_filename'] = yaml_file.name
                            data['_submission_status'] = 'community'
                            submissions.append(data)
                except Exception as e:
                    print(f"Error loading {yaml_file}: {e}")
                    continue
            
            # Sort by annotation_date (newest first)
            submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return submissions
        except Exception as e:
            raise Exception(f"Error loading community submissions: {str(e)}")
    
    def get_approved_submissions(self, dandiset_id: str) -> List[Dict[str, Any]]:
        """
        Get all approved submissions for a dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            
        Returns:
            List of approved submission data with metadata
        """
        try:
            approved_dir = self._get_approved_dir(dandiset_id)
            submissions = []
            
            for yaml_file in approved_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as file:
                        data = yaml.safe_load(file)
                        if data:
                            # Add metadata about the submission
                            data['_submission_filename'] = yaml_file.name
                            data['_submission_status'] = 'approved'
                            submissions.append(data)
                except Exception as e:
                    print(f"Error loading {yaml_file}: {e}")
                    continue
            
            # Sort by annotation_date (newest first)
            submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return submissions
        except Exception as e:
            raise Exception(f"Error loading approved submissions: {str(e)}")
    
    def approve_submission(self, dandiset_id: str, filename: str, approver_info: Dict[str, Any]) -> bool:
        """
        Move a submission from community to approved folder and add approval information
        
        Args:
            dandiset_id: The dandiset identifier
            filename: The filename of the submission to approve
            approver_info: Information about the person approving (name, email, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            community_dir = self._get_community_dir(dandiset_id)
            approved_dir = self._get_approved_dir(dandiset_id)
            
            source_path = community_dir / filename
            dest_path = approved_dir / filename
            
            if not source_path.exists():
                raise FileNotFoundError(f"Submission file not found: {filename}")
            
            if dest_path.exists():
                raise FileExistsError(f"File already exists in approved folder: {filename}")
            
            # Load the existing submission data
            with open(source_path, 'r', encoding='utf-8') as file:
                submission_data = yaml.safe_load(file)
            
            # Add approval information
            submission_data['approval_contributor'] = {
                'name': approver_info.get('name', 'Unknown Moderator'),
                'email': approver_info.get('email'),
                'identifier': approver_info.get('identifier'),
                'url': approver_info.get('url'),
                'schemaKey': 'AnnotationContributor'
            }
            submission_data['approval_date'] = datetime.now().astimezone().isoformat()
            
            # Save the updated data to the approved folder
            with open(dest_path, 'w', encoding='utf-8') as file:
                yaml.dump(submission_data, file, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
            
            # Remove the original file from community folder
            source_path.unlink()
            
            return True
            
        except Exception as e:
            raise Exception(f"Error approving submission: {str(e)}")
    
    def get_all_pending_submissions(self) -> List[Dict[str, Any]]:
        """
        Get all pending community submissions across all dandisets
        
        Returns:
            List of all community submissions with dandiset info
        """
        try:
            all_submissions = []
            
            # Iterate through all dandiset directories
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    community_submissions = self.get_community_submissions(dandiset_id)
                    
                    # Add dandiset info to each submission
                    for submission in community_submissions:
                        submission['_dandiset_id'] = dandiset_id
                        all_submissions.append(submission)
            
            # Sort by annotation_date (newest first)
            all_submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return all_submissions
            
        except Exception as e:
            raise Exception(f"Error loading all pending submissions: {str(e)}")
    
    def get_submission_by_filename(self, dandiset_id: str, filename: str, status: str = 'community') -> Optional[Dict[str, Any]]:
        """
        Get a specific submission by filename
        
        Args:
            dandiset_id: The dandiset identifier
            filename: The submission filename
            status: 'community' or 'approved'
            
        Returns:
            The submission data or None if not found
        """
        try:
            if status == 'community':
                target_dir = self._get_community_dir(dandiset_id)
            else:
                target_dir = self._get_approved_dir(dandiset_id)
            
            filepath = target_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                if data:
                    data['_submission_filename'] = filename
                    data['_submission_status'] = status
                    data['_dandiset_id'] = dandiset_id
                return data
                
        except Exception as e:
            print(f"Error loading submission {filename}: {e}")
            return None
    
    def get_all_dandisets(self) -> List[Dict[str, Any]]:
        """
        Get all dandisets that have submissions (community or approved)
        
        Returns:
            List of dandiset info with submission counts
        """
        try:
            dandisets = []
            
            # Iterate through all dandiset directories
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    
                    # Count submissions
                    community_count = len(self.get_community_submissions(dandiset_id))
                    approved_count = len(self.get_approved_submissions(dandiset_id))
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
            
        except Exception as e:
            raise Exception(f"Error loading dandisets: {str(e)}")
    
    def _paginate_list(self, items: List[Any], page: int = 1, per_page: int = 10) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Paginate a list of items and return pagination metadata
        
        Args:
            items: List of items to paginate
            page: Current page number (1-based)
            per_page: Number of items per page
            
        Returns:
            Tuple of (paginated_items, pagination_info)
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
        Get paginated dandisets that have submissions
        
        Args:
            page: Current page number (1-based)
            per_page: Number of dandisets per page
            
        Returns:
            Tuple of (paginated_dandisets, pagination_info)
        """
        all_dandisets = self.get_all_dandisets()
        return self._paginate_list(all_dandisets, page, per_page)
    
    def get_community_submissions_paginated(self, dandiset_id: str, page: int = 1, per_page: int = 9) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get paginated community submissions for a dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            page: Current page number (1-based)
            per_page: Number of submissions per page
            
        Returns:
            Tuple of (paginated_submissions, pagination_info)
        """
        all_submissions = self.get_community_submissions(dandiset_id)
        return self._paginate_list(all_submissions, page, per_page)
    
    def get_approved_submissions_paginated(self, dandiset_id: str, page: int = 1, per_page: int = 9) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get paginated approved submissions for a dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            page: Current page number (1-based)
            per_page: Number of submissions per page
            
        Returns:
            Tuple of (paginated_submissions, pagination_info)
        """
        all_submissions = self.get_approved_submissions(dandiset_id)
        return self._paginate_list(all_submissions, page, per_page)
    
    def get_all_pending_submissions_paginated(self, page: int = 1, per_page: int = 9) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get paginated pending community submissions across all dandisets
        
        Args:
            page: Current page number (1-based)
            per_page: Number of submissions per page
            
        Returns:
            Tuple of (paginated_submissions, pagination_info)
        """
        all_submissions = self.get_all_pending_submissions()
        return self._paginate_list(all_submissions, page, per_page)
    
    def get_user_submissions(self, user_email: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get all submissions (community and approved) for a specific user
        
        Args:
            user_email: Email address of the user
            
        Returns:
            Tuple of (community_submissions, approved_submissions)
        """
        try:
            community_submissions = []
            approved_submissions = []
            
            # Iterate through all dandiset directories
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    
                    # Get community submissions for this dandiset
                    dandiset_community = self.get_community_submissions(dandiset_id)
                    for submission in dandiset_community:
                        contributor_email = submission.get('annotation_contributor', {}).get('email', '')
                        if contributor_email == user_email:
                            submission['_dandiset_id'] = dandiset_id
                            community_submissions.append(submission)
                    
                    # Get approved submissions for this dandiset
                    dandiset_approved = self.get_approved_submissions(dandiset_id)
                    for submission in dandiset_approved:
                        contributor_email = submission.get('annotation_contributor', {}).get('email', '')
                        if contributor_email == user_email:
                            submission['_dandiset_id'] = dandiset_id
                            approved_submissions.append(submission)
            
            # Sort by annotation_date (newest first)
            community_submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            approved_submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            
            return community_submissions, approved_submissions
            
        except Exception as e:
            raise Exception(f"Error loading user submissions: {str(e)}")
    
    def get_user_submissions_paginated(self, user_email: str, community_page: int = 1, approved_page: int = 1, per_page: int = 9) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get paginated submissions for a specific user
        
        Args:
            user_email: Email address of the user
            community_page: Current page for community submissions
            approved_page: Current page for approved submissions
            per_page: Number of submissions per page
            
        Returns:
            Tuple of (community_submissions, community_pagination, approved_submissions, approved_pagination)
        """
        community_submissions, approved_submissions = self.get_user_submissions(user_email)
        
        community_paginated, community_pagination = self._paginate_list(community_submissions, community_page, per_page)
        approved_paginated, approved_pagination = self._paginate_list(approved_submissions, approved_page, per_page)
        
        return community_paginated, community_pagination, approved_paginated, approved_pagination
    
    def get_dandiset(self, dandiset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific dandiset by ID
        
        Args:
            dandiset_id: The dandiset identifier
            
        Returns:
            Dandiset info dict or None if not found
        """
        try:
            all_dandisets = self.get_all_dandisets()
            for dandiset in all_dandisets:
                if dandiset.get('id') == dandiset_id:
                    return dandiset
            return None
        except Exception as e:
            raise Exception(f"Error retrieving dandiset {dandiset_id}: {str(e)}")
    
    def get_resource_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific resource by ID across all dandisets
        
        Args:
            resource_id: The resource identifier (filename without .yaml extension)
            
        Returns:
            Resource data dict or None if not found
        """
        try:
            # Search through all dandisets for this resource
            all_dandisets = self.get_all_dandisets()
            
            for dandiset in all_dandisets:
                dandiset_id = dandiset['id']
                
                # Check approved submissions
                approved_submissions = self.get_approved_submissions(dandiset_id)
                for submission in approved_submissions:
                    if submission.get('_submission_filename', '').replace('.yaml', '') == resource_id:
                        return submission
                
                # Check community submissions
                community_submissions = self.get_community_submissions(dandiset_id)
                for submission in community_submissions:
                    if submission.get('_submission_filename', '').replace('.yaml', '') == resource_id:
                        return submission
            
            return None
        except Exception as e:
            raise Exception(f"Error retrieving resource {resource_id}: {str(e)}")
    
    def get_all_submissions(self, dandiset_id: str, include_community: bool = True) -> List[Dict[str, Any]]:
        """
        Get all submissions (approved + community) for a dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            include_community: Whether to include community submissions
            
        Returns:
            List of all submission data
        """
        try:
            # Get approved submissions
            approved_submissions = self.get_approved_submissions(dandiset_id)
            
            # Get community submissions if requested
            community_submissions = []
            if include_community:
                community_submissions = self.get_community_submissions(dandiset_id)
            
            # Combine and sort by annotation_date (newest first)
            all_submissions = approved_submissions + community_submissions
            all_submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            
            return all_submissions
        except Exception as e:
            raise Exception(f"Error retrieving all submissions for dandiset {dandiset_id}: {str(e)}")
    
    def get_all_submissions_paginated(self, dandiset_id: str, page: int = 1, per_page: int = 10, include_community: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get paginated submissions (approved + community) for a dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            page: Current page number (1-based)
            per_page: Number of submissions per page
            include_community: Whether to include community submissions
            
        Returns:
            Tuple of (paginated_submissions, pagination_info)
        """
        all_submissions = self.get_all_submissions(dandiset_id, include_community)
        return self._paginate_list(all_submissions, page, per_page)
    
    def get_dandiset_stats(self, dandiset_id: str) -> Dict[str, Any]:
        """
        Get detailed statistics for a specific dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            
        Returns:
            Dictionary with detailed dandiset statistics
        """
        try:
            # Get dandiset information
            dandiset_info = self.get_dandiset(dandiset_id)
            if not dandiset_info:
                raise Exception(f"Dandiset {dandiset_id} not found")
            
            # Get detailed submissions for analysis
            approved_submissions = self.get_approved_submissions(dandiset_id)
            community_submissions = self.get_community_submissions(dandiset_id)
            
            # Calculate detailed statistics
            stats = {
                'dandiset_id': dandiset_id,
                'display_id': f"DANDI:{dandiset_id.split('_')[1]}" if '_' in dandiset_id else f"DANDI:{dandiset_id.zfill(6)}",
                'approved_count': len(approved_submissions),
                'pending_count': len(community_submissions),
                'total_count': len(approved_submissions) + len(community_submissions),
                'unique_contributors': len(set(
                    submission.get('annotation_contributor', {}).get('name')
                    for submission in approved_submissions + community_submissions
                    if submission.get('annotation_contributor', {}).get('name')
                )),
                'resource_types': {},
                'repositories': {}
            }
            
            # Analyze resource types and repositories
            all_submissions = approved_submissions + community_submissions
            for submission in all_submissions:
                resource_type = submission.get('resourceType', 'Unknown')
                repository = submission.get('repository', 'Unknown')
                
                stats['resource_types'][resource_type] = stats['resource_types'].get(resource_type, 0) + 1
                stats['repositories'][repository] = stats['repositories'].get(repository, 0) + 1
            
            return stats
        except Exception as e:
            raise Exception(f"Error calculating dandiset statistics: {str(e)}")
