"""
JSON serialization helpers for API responses
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json


def serialize_datetime(dt: datetime) -> str:
    """
    Serialize datetime to ISO format string
    
    Args:
        dt: Datetime object to serialize
    
    Returns:
        ISO format datetime string
    """
    if dt is None:
        return None
    return dt.isoformat()


def serialize_external_resource(resource: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize an external resource for API response
    
    Args:
        resource: Resource dictionary from submission handler
    
    Returns:
        Serialized resource data
    """
    if not resource:
        return None
    
    # Create a copy to avoid modifying original
    serialized = resource.copy()
    
    # Handle datetime fields
    if 'annotation_date' in serialized and isinstance(serialized['annotation_date'], datetime):
        serialized['annotation_date'] = serialize_datetime(serialized['annotation_date'])
    
    if 'approval_date' in serialized and isinstance(serialized['approval_date'], datetime):
        serialized['approval_date'] = serialize_datetime(serialized['approval_date'])
    
    # Ensure consistent field names
    if '_dandiset_id' in serialized:
        serialized['dandiset_id'] = serialized.pop('_dandiset_id')
    
    if '_filename' in serialized:
        serialized['filename'] = serialized.pop('_filename')
    
    if '_status' in serialized:
        serialized['status'] = serialized.pop('_status')
    
    # Add resource ID if not present (use filename as fallback)
    if 'id' not in serialized and 'filename' in serialized:
        serialized['id'] = serialized['filename'].replace('.yaml', '')
    
    return serialized


def serialize_external_resources(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize a list of external resources
    
    Args:
        resources: List of resource dictionaries
    
    Returns:
        List of serialized resource data
    """
    return [serialize_external_resource(resource) for resource in resources if resource]


def serialize_dandiset_info(dandiset_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize dandiset information for API response
    
    Args:
        dandiset_data: Dandiset data from submission handler
    
    Returns:
        Serialized dandiset data
    """
    if not dandiset_data:
        return None
    
    # Create a copy to avoid modifying original
    serialized = dandiset_data.copy()
    
    # Format display ID
    dandiset_id = serialized.get('dandiset_id', '')
    if dandiset_id:
        if '_' in dandiset_id:
            display_id = f"DANDI:{dandiset_id.split('_')[1]}"
        else:
            display_id = f"DANDI:{dandiset_id.zfill(6)}"
        serialized['display_id'] = display_id
    
    return serialized


def serialize_dandisets(dandisets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize a list of dandisets
    
    Args:
        dandisets: List of dandiset dictionaries
    
    Returns:
        List of serialized dandiset data
    """
    return [serialize_dandiset_info(dandiset) for dandiset in dandisets if dandiset]


def serialize_user_info(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize user information for API response (excluding sensitive data)
    
    Args:
        user_data: User data dictionary
    
    Returns:
        Serialized user data (without password)
    """
    if not user_data:
        return None
    
    # Create a copy and remove sensitive fields
    serialized = user_data.copy()
    
    # Remove password and other sensitive fields
    sensitive_fields = ['password', 'password_hash', 'salt']
    for field in sensitive_fields:
        serialized.pop(field, None)
    
    return serialized


def serialize_submission_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize submission statistics for API response
    
    Args:
        stats: Statistics dictionary
    
    Returns:
        Serialized statistics data
    """
    if not stats:
        return {}
    
    serialized = stats.copy()
    
    # Handle datetime fields in stats if present
    for key, value in serialized.items():
        if isinstance(value, datetime):
            serialized[key] = serialize_datetime(value)
    
    return serialized


def serialize_pagination_info(pagination: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize pagination information for API response
    
    Args:
        pagination: Pagination dictionary from submission handler
    
    Returns:
        Serialized pagination data
    """
    if not pagination:
        return None
    
    return {
        'page': pagination.get('page', 1),
        'per_page': pagination.get('per_page', 10),
        'total_items': pagination.get('total_items', 0),
        'total_pages': pagination.get('total_pages', 1),
        'has_prev': pagination.get('has_prev', False),
        'has_next': pagination.get('has_next', False),
        'prev_page': pagination.get('prev_page'),
        'next_page': pagination.get('next_page'),
        'start_item': pagination.get('start_item', 0),
        'end_item': pagination.get('end_item', 0)
    }


def serialize_validation_error(error: Exception) -> Dict[str, Any]:
    """
    Serialize validation error for API response
    
    Args:
        error: Validation error exception
    
    Returns:
        Serialized error data
    """
    error_data = {
        'type': type(error).__name__,
        'message': str(error)
    }
    
    # Handle Pydantic validation errors
    if hasattr(error, 'errors'):
        try:
            error_data['details'] = error.errors()
        except:
            error_data['details'] = str(error)
    
    return error_data


class APIJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for API responses that handles datetime objects
    """
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return serialize_datetime(obj)
        return super().default(obj)
