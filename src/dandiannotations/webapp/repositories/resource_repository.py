import os
import yaml
import shutil
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import uuid

# Import for type hinting
from dandiannotations.models.models import ExternalResource


class ResourceRepository:
    def __init__(self, base_submissions_dir: str):
        """
        Initialize the repository

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

    def save_resource(self, dandiset_id: str, external_resource: ExternalResource) -> str:
        """
        Save a new community submission

        Args:
            dandiset_id: The dandiset identifier
            external_resource: The ExternalResource Pydantic model to save

        Returns:
            The resource ID of the saved resource
        """
        community_dir = self._get_community_dir(dandiset_id)
        resource_id = str(uuid.uuid4())
        filename = f"{resource_id}.yaml"
        filepath = community_dir / filename

        # Convert Pydantic model to dict for YAML serialization
        resource_data = external_resource.model_dump(mode='json', exclude_none=True)

        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(resource_data, file, default_flow_style=False,
                        allow_unicode=True, sort_keys=False, indent=2)

        return resource_id

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
         
    def delete_submission(self, dandiset_id: str, filename: str, status: str, moderator_info: Dict[str, Any]) -> bool:
        """
        Delete a submission and move it to backup folder with audit trail

        Args:
            dandiset_id: The dandiset identifier
            filename: The submission filename to delete
            status: 'community' or 'approved'
            moderator_info: Information about the moderator performing deletion

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get source directory based on status
            if status == 'community':
                source_dir = self._get_community_dir(dandiset_id)
            elif status == 'approved':
                source_dir = self._get_approved_dir(dandiset_id)
            else:
                raise ValueError(f"Invalid status: {status}. Must be 'community' or 'approved'")

            # Get source file path
            source_path = source_dir / filename

            if not source_path.exists():
                raise FileNotFoundError(f"Submission file not found: {filename}")

            # Create deleted directory structure
            dandiset_dir = self._get_dandiset_dir(dandiset_id)
            deleted_dir = dandiset_dir / "deleted" / status
            deleted_dir.mkdir(parents=True, exist_ok=True)

            # Generate timestamped filename for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"deleted_{timestamp}_{filename}"
            backup_path = deleted_dir / backup_filename

            # Load the existing submission data
            with open(source_path, 'r', encoding='utf-8') as file:
                submission_data = yaml.safe_load(file)

            # Add deletion metadata
            submission_data['deletion_info'] = {
                'deleted_by': {
                    'name': moderator_info.get('name', 'Unknown Moderator'),
                    'email': moderator_info.get('email'),
                    'identifier': moderator_info.get('identifier'),
                    'url': moderator_info.get('url'),
                    'schemaKey': 'AnnotationContributor'
                },
                'deletion_date': datetime.now().astimezone().isoformat(),
                'original_filename': filename,
                'original_status': status
            }

            # Save the updated data to the backup folder
            with open(backup_path, 'w', encoding='utf-8') as file:
                yaml.dump(submission_data, file, default_flow_style=False,
                         allow_unicode=True, sort_keys=False, indent=2)

            # Remove the original file
            source_path.unlink()

            return True

        except Exception as e:
            raise Exception(f"Error deleting submission: {str(e)}")
     
    def get_all_submissions(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all submissions across all dandisets for the given status.

        Args:
            status: 'community' or 'approved'

        Returns:
            List of all submissions with dandiset info for the specified status
        """
        try:
            status_norm = (status or '').strip().lower()
            if status_norm not in {'community', 'approved'}:
                raise ValueError("Invalid status: must be 'community' or 'approved'")

            all_submissions: List[Dict[str, Any]] = []

            # Iterate through all dandiset directories
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name
                    submissions = self.get_submissions_by_dandiset(dandiset_id, status_norm)

                    # Add dandiset info to each submission
                    for submission in submissions:
                        submission['_dandiset_id'] = dandiset_id
                        all_submissions.append(submission)

            # Sort by annotation_date (newest first)
            all_submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return all_submissions

        except Exception as e:
            raise Exception(f"Error loading all {status} submissions: {str(e)}")

    def get_submissions_by_dandiset(self, dandiset_id: str, status: str) -> List[Dict[str, Any]]:
        """
        Get submissions for a dandiset by status.

        Args:
            dandiset_id: The dandiset identifier
            status: 'community' or 'approved'

        Returns:
            List of submission data with metadata for the requested status
        """
        try:
            status_norm = (status or '').strip().lower()
            if status_norm not in {'community', 'approved'}:
                raise ValueError("Invalid status: must be 'community' or 'approved'")

            target_dir = self._get_community_dir(dandiset_id) if status_norm == 'community' else self._get_approved_dir(dandiset_id)
            submissions: List[Dict[str, Any]] = []

            for yaml_file in target_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as file:
                        data = yaml.safe_load(file)
                        if data:
                            # Add metadata about the submission
                            data['_submission_filename'] = yaml_file.name
                            data['_submission_status'] = status_norm
                            submissions.append(data)
                except Exception as e:
                    print(f"Error loading {yaml_file}: {e}")
                    continue

            # Sort by annotation_date (newest first)
            submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return submissions
        except Exception as e:
            raise Exception(f"Error loading {status} submissions: {str(e)}")

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

    def get_submissions_by_user(self, user_email: str, status: str) -> List[Dict[str, Any]]:
        """
        Get submissions for a specific user by status across all dandisets.

        Args:
            user_email: Email address of the user
            status: 'community' or 'approved'

        Returns:
            List of submissions for the user across all dandisets.
        """
        try:
            status_norm = (status or '').strip().lower()
            if status_norm not in {'community', 'approved'}:
                raise ValueError("Invalid status: must be 'community' or 'approved'")

            collected: List[Dict[str, Any]] = []

            # Iterate through all dandiset directories
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.startswith('dandiset_'):
                    dandiset_id = dandiset_dir.name

                    # Get submissions for this dandiset by status
                    dandiset_submissions = self.get_submissions_by_dandiset(dandiset_id, status_norm)
                    for submission in dandiset_submissions:
                        contributor_email = submission.get('annotation_contributor', {}).get('email', '')
                        if contributor_email == user_email:
                            submission['_dandiset_id'] = dandiset_id
                            collected.append(submission)

            # Sort by annotation_date (newest first)
            collected.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return collected

        except Exception as e:
            raise Exception(f"Error loading user {status} submissions: {str(e)}")
