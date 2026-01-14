import os
import yaml
import shutil
import math
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import uuid
from yaml import YAMLError
from pydantic import ValidationError

# Import for type hinting
from dandiannotations.models.models import ExternalResource, AnnotationContributor


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
        # Ensure 6-digit format with zero padding
        dandiset_id = dandiset_id.zfill(6)
        return self.base_dir / dandiset_id

    def _get_pending_dir(self, dandiset_id: str) -> Path:
        """Get the pending resources directory for a dandiset"""
        dandiset_dir = self._get_dandiset_dir(dandiset_id)
        pending_dir = dandiset_dir / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        return pending_dir

    def _get_approved_dir(self, dandiset_id: str) -> Path:
        """Get the approved submissions directory for a dandiset"""
        dandiset_dir = self._get_dandiset_dir(dandiset_id)
        approved_dir = dandiset_dir / "approved"
        approved_dir.mkdir(parents=True, exist_ok=True)
        return approved_dir

    def _get_resource_path(self, dandiset_id: str, status: str, resource_uuid: str) -> Path:
        """
        Compute the full path to a resource YAML given dandiset, status, and UUID.
        """
        if status not in {'pending', 'approved'}:
            raise ValueError("Invalid status: must be 'pending' or 'approved'")
        base_dir = self._get_pending_dir(dandiset_id) if status == 'pending' else self._get_approved_dir(dandiset_id)
        filename = f"{resource_uuid}.yaml"
        return base_dir / filename
    
    def get_all_dandiset_ids(self) -> List[str]:
        """
        Return a list of 6-digit dandiset IDs (e.g., '000001') present under base_dir.
        """
        dandiset_ids: List[str] = []
        for dandiset_dir in self.base_dir.iterdir():
            if dandiset_dir.is_dir() and dandiset_dir.name.isdigit() and len(dandiset_dir.name) == 6:
                dandiset_ids.append(dandiset_dir.name)
        dandiset_ids.sort()
        return dandiset_ids

    def save_resource(self, dandiset_id: str, external_resource: ExternalResource) -> str:
        """
        Save a new pending resource

        Args:
            dandiset_id: The dandiset identifier
            external_resource: The ExternalResource Pydantic model to save

        Returns:
            The resource UUID (as a string) of the saved resource
        """
        pending_dir = self._get_pending_dir(dandiset_id)
        resource_uuid = str(external_resource.uuid)
        filename = f"{resource_uuid}.yaml"
        filepath = pending_dir / filename

        # Convert Pydantic model to dict for YAML serialization
        resource_data = external_resource.model_dump(mode='json', exclude_none=True)

        with open(filepath, 'w', encoding='utf-8') as file:
            yaml.dump(resource_data, file, default_flow_style=False,
                        allow_unicode=True, sort_keys=False, indent=2)

        return resource_uuid

    def approve_submission(self, dandiset_id: str, resource_uuid: str, approver: AnnotationContributor) -> bool:
        """
        Move a submission from pending to approved folder and add approval information using UUID.
        """
        try:
            source_path = self._get_resource_path(dandiset_id, 'pending', resource_uuid)
            dest_path = self._get_resource_path(dandiset_id, 'approved', resource_uuid)

            if not source_path.exists():
                raise FileNotFoundError(f"Submission file not found: {resource_uuid}.yaml")

            if dest_path.exists():
                raise FileExistsError(f"File already exists in approved folder: {resource_uuid}.yaml")

            # Load and validate the existing submission as ExternalResource
            with open(source_path, 'r', encoding='utf-8') as file:
                submission_data = yaml.safe_load(file) or {}
            resource = ExternalResource.model_validate(submission_data)

            # Set approval fields using Pydantic models
            resource.approval_contributor = approver
            resource.approval_date = datetime.now().astimezone()

            # Save the updated data to the approved folder
            updated_data = resource.model_dump(mode='json', exclude_none=True)
            with open(dest_path, 'w', encoding='utf-8') as file:
                yaml.dump(updated_data, file, default_flow_style=False,
                          allow_unicode=True, sort_keys=False, indent=2)

            # Remove the original file from pending folder
            source_path.unlink()

            return True

        except Exception as e:
            raise Exception(f"Error approving submission: {str(e)}")
         
    def delete_submission(self, dandiset_id: str, resource_uuid: str, status: str, moderator: AnnotationContributor) -> bool:
        """
        Delete a resource (pending or approved) by UUID and move it to backup folder with audit trail.
        """
        try:
            if status not in {'pending', 'approved'}:
                raise ValueError(f"Invalid status: {status}. Must be 'pending' or 'approved'")

            # Get source file path
            source_path = self._get_resource_path(dandiset_id, status, resource_uuid)

            if not source_path.exists():
                raise FileNotFoundError(f"Submission file not found: {resource_uuid}.yaml")

            # Create deleted directory structure
            dandiset_dir = self._get_dandiset_dir(dandiset_id)
            deleted_dir = dandiset_dir / "deleted" / status
            deleted_dir.mkdir(parents=True, exist_ok=True)

            # Generate timestamped filename for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"deleted_{timestamp}_{resource_uuid}.yaml"
            backup_path = deleted_dir / backup_filename

            # Load and validate the existing submission as ExternalResource
            with open(source_path, 'r', encoding='utf-8') as file:
                submission_data = yaml.safe_load(file) or {}
            resource = ExternalResource.model_validate(submission_data)

            # Compose deletion audit info using Pydantic models
            deletion_info = {
                'deleted_by': moderator.model_dump(mode='json', exclude_none=True),
                'deletion_date': datetime.now().astimezone().isoformat(),
                'original_filename': f"{resource_uuid}.yaml",
                'original_status': status
            }

            # Prepare backup payload and write to backup folder
            backup_payload = resource.model_dump(mode='json', exclude_none=True)
            backup_payload['deletion_info'] = deletion_info
            with open(backup_path, 'w', encoding='utf-8') as file:
                yaml.dump(backup_payload, file, default_flow_style=False,
                          allow_unicode=True, sort_keys=False, indent=2)

            # Remove the original file
            source_path.unlink()

            return True

        except Exception as e:
            raise Exception(f"Error deleting submission: {str(e)}")
     
    def get_all_resources(self, status: str) -> List[ExternalResource]:
        """
        Get all resources across all dandisets for the given status.

        Args:
            status: 'pending' or 'approved'

        Returns:
            List of all resources with dandiset info for the specified status
        """
        try:
            if status not in {'pending', 'approved'}:
                raise ValueError("Invalid status: must be 'pending' or 'approved'")

            all_resources: List[ExternalResource] = []

            # Iterate through all dandiset directories (6-digit IDs)
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.isdigit() and len(dandiset_dir.name) == 6:
                    dandiset_id = dandiset_dir.name
                    resources = self.get_resources_by_dandiset(dandiset_id, status)

                    # Add dandiset info to each resource
                    for res in resources:
                        all_resources.append(res)

            # Sort by annotation_date (newest first)
            all_resources.sort(key=lambda r: r.annotation_date.isoformat() if getattr(r, 'annotation_date', None) else '', reverse=True)
            return all_resources

        except Exception as e:
            raise Exception(f"Error loading all {status} resources: {str(e)}")

    def get_resources_by_dandiset(self, dandiset_id: str, status: str) -> List[ExternalResource]:
        """
        Get resources for a dandiset by status.

        Args:
            dandiset_id: The dandiset identifier
            status: 'pending' or 'approved'

        Returns:
            List of resource data with metadata for the requested status
        """
        try:
            if status not in {'pending', 'approved'}:
                raise ValueError("Invalid status: must be 'pending' or 'approved'")

            target_dir = self._get_pending_dir(dandiset_id) if status == 'pending' else self._get_approved_dir(dandiset_id)
            resources: List[ExternalResource] = []

            for yaml_file in target_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as file:
                        loaded = yaml.safe_load(file) or {}
                    resource = ExternalResource.model_validate(loaded)
                    resources.append(resource)
                except ValidationError as e:
                    print(f"Validation error in {yaml_file}: {e}")
                    continue
                except (OSError, YAMLError) as e:
                    print(f"Error loading {yaml_file}: {e}")
                    continue
                except Exception as e:
                    print(f"Unexpected error processing {yaml_file}: {e}")
                    continue

            # Sort by annotation_date (newest first)
            resources.sort(key=lambda r: r.annotation_date.isoformat() if getattr(r, 'annotation_date', None) else '', reverse=True)
            return resources
        except Exception as e:
            raise Exception(f"Error loading {status} resources: {str(e)}")

    def get_resource_by_uuid(self, dandiset_id: str, resource_uuid: str, status: str = 'pending') -> ExternalResource:
        """
        Get a specific resource by UUID.

        Returns:
            ExternalResource

        Raises:
            FileNotFoundError: If the resource YAML does not exist.
            Exception: If an error occurs while reading or validating the YAML.
        """
        try:
            filepath = self._get_resource_path(dandiset_id, status, resource_uuid)

            if not filepath.exists():
                raise FileNotFoundError(f"Submission file not found: {resource_uuid}.yaml")

            with open(filepath, 'r', encoding='utf-8') as file:
                loaded = yaml.safe_load(file) or {}
            resource = ExternalResource.model_validate(loaded)
            return resource

        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Error loading resource {resource_uuid}: {str(e)}")

    def get_resources_by_user(self, user_email: str, status: str) -> List[ExternalResource]:
        """
        Get resources for a specific user by status across all dandisets.

        Args:
            user_email: Email address of the user
            status: 'pending' or 'approved'

        Returns:
            List of resources for the user across all dandisets.
        """
        try:
            if status not in {'pending', 'approved'}:
                raise ValueError("Invalid status: must be 'pending' or 'approved'")

            collected: List[ExternalResource] = []

            # Iterate through all dandiset directories (6-digit IDs)
            for dandiset_dir in self.base_dir.iterdir():
                if dandiset_dir.is_dir() and dandiset_dir.name.isdigit() and len(dandiset_dir.name) == 6:
                    dandiset_id = dandiset_dir.name

                    # Get resources for this dandiset by status
                    dandiset_resources = self.get_resources_by_dandiset(dandiset_id, status)
                    for res in dandiset_resources:
                        try:
                            contributor_email = str(res.annotation_contributor.email)
                        except Exception:
                            contributor_email = ''
                        if contributor_email == user_email:
                            collected.append(res)

            # Sort by annotation_date (newest first)
            collected.sort(key=lambda r: r.annotation_date.isoformat() if getattr(r, 'annotation_date', None) else '', reverse=True)
            return collected

        except Exception as e:
            raise Exception(f"Error loading user {status} resources: {str(e)}")
