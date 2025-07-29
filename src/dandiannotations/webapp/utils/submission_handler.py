"""
Submission handling utilities for the two-tiered external resources system
"""
import os
import yaml
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional
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
    
    def _get_endorsed_dir(self, dandiset_id: str) -> Path:
        """Get the endorsed submissions directory for a dandiset"""
        dandiset_dir = self._get_dandiset_dir(dandiset_id)
        endorsed_dir = dandiset_dir / "endorsed"
        endorsed_dir.mkdir(parents=True, exist_ok=True)
        return endorsed_dir
    
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
    
    def get_endorsed_submissions(self, dandiset_id: str) -> List[Dict[str, Any]]:
        """
        Get all endorsed submissions for a dandiset
        
        Args:
            dandiset_id: The dandiset identifier
            
        Returns:
            List of endorsed submission data with metadata
        """
        try:
            endorsed_dir = self._get_endorsed_dir(dandiset_id)
            submissions = []
            
            for yaml_file in endorsed_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as file:
                        data = yaml.safe_load(file)
                        if data:
                            # Add metadata about the submission
                            data['_submission_filename'] = yaml_file.name
                            data['_submission_status'] = 'endorsed'
                            submissions.append(data)
                except Exception as e:
                    print(f"Error loading {yaml_file}: {e}")
                    continue
            
            # Sort by annotation_date (newest first)
            submissions.sort(key=lambda x: x.get('annotation_date', ''), reverse=True)
            return submissions
        except Exception as e:
            raise Exception(f"Error loading endorsed submissions: {str(e)}")
    
    def endorse_submission(self, dandiset_id: str, filename: str) -> bool:
        """
        Move a submission from community to endorsed folder
        
        Args:
            dandiset_id: The dandiset identifier
            filename: The filename of the submission to endorse
            
        Returns:
            True if successful, False otherwise
        """
        try:
            community_dir = self._get_community_dir(dandiset_id)
            endorsed_dir = self._get_endorsed_dir(dandiset_id)
            
            source_path = community_dir / filename
            dest_path = endorsed_dir / filename
            
            if not source_path.exists():
                raise FileNotFoundError(f"Submission file not found: {filename}")
            
            if dest_path.exists():
                raise FileExistsError(f"File already exists in endorsed folder: {filename}")
            
            # Move the file
            shutil.move(str(source_path), str(dest_path))
            return True
            
        except Exception as e:
            raise Exception(f"Error endorsing submission: {str(e)}")
    
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
            status: 'community' or 'endorsed'
            
        Returns:
            The submission data or None if not found
        """
        try:
            if status == 'community':
                target_dir = self._get_community_dir(dandiset_id)
            else:
                target_dir = self._get_endorsed_dir(dandiset_id)
            
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
