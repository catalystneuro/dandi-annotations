"""
API-specific validation helpers
"""

from typing import Any, Dict, List, Optional, Tuple
from flask import request
import re
from dandiannotations.models.models import ExternalResource, AnnotationContributor
from pydantic import ValidationError


def validate_json_request() -> Tuple[bool, Optional[str]]:
    """
    Validate that request contains valid JSON
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not request.is_json:
        return False, "Request must contain valid JSON"
    
    try:
        request.get_json()
        return True, None
    except Exception as e:
        return False, f"Invalid JSON: {str(e)}"


def validate_pagination_params(
    page: int,
    per_page: int,
) -> Tuple[bool, Optional[str]]:
    """
    Validate pagination parameters
    
    Args:
        page: Page number
        per_page: Items per page
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate page
    if not isinstance(page, int):
        return False, "Page must be an integer"

    if page < 1:
        return False, "Page must be >= 1"

    # Validate per_page
    if not isinstance(per_page, int):
        return False, "Per page must be an integer"

    if per_page < 1:
        return False, "Per page must be >= 1"

    return True, None


def validate_dandiset_id(dandiset_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate dandiset ID format
    
    Args:
        dandiset_id: Dandiset ID to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not dandiset_id:
        return False, "Dandiset ID is required"
    
    # Accept either 6-digit format (000001) or full format (dandiset_000001)
    pattern = r'^(dandiset_)?[0-9]{6}$'
    if not re.match(pattern, dandiset_id):
        return False, "Invalid dandiset ID format. Use 6 digits (e.g., 000001) or full format (e.g., dandiset_000001)"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email format
    
    Args:
        email: Email address to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    
    return True, None


def validate_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL format
    
    Args:
        url: URL to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        return False, "URL is required"
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, url):
        return False, "Invalid URL format. Must start with http:// or https://"
    
    return True, None


def validate_orcid(orcid: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate ORCID format
    
    Args:
        orcid: ORCID identifier to validate (optional)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not orcid:
        return True, None  # ORCID is optional
    
    pattern = r'^https://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
    if not re.match(pattern, orcid):
        return False, "Invalid ORCID format. Should be like: https://orcid.org/0000-0000-0000-0000"
    
    return True, None


def validate_resource_submission(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate resource submission data
    
    Args:
        data: Resource submission data
    
    Returns:
        Tuple of (is_valid, error_message, validation_details)
    """
    # Check required fields
    required_fields = [
        'resource_name', 'resource_url', 'repository', 'relation', 
        'resource_type', 'contributor_name', 'contributor_email'
    ]
    
    missing_fields = []
    for field in required_fields:
        if not data.get(field, '').strip():
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}", {
            'missing_fields': missing_fields
        }
    
    # Validate email format
    is_valid, error = validate_email(data['contributor_email'])
    if not is_valid:
        return False, f"Invalid contributor email: {error}", None
    
    # Validate URLs
    is_valid, error = validate_url(data['resource_url'])
    if not is_valid:
        return False, f"Invalid resource URL: {error}", None
    
    if data.get('contributor_url'):
        is_valid, error = validate_url(data['contributor_url'])
        if not is_valid:
            return False, f"Invalid contributor URL: {error}", None
    
    # Validate ORCID if provided
    is_valid, error = validate_orcid(data.get('contributor_identifier'))
    if not is_valid:
        return False, f"Invalid ORCID: {error}", None
    
    return True, None, None


def validate_with_pydantic_model(data: Dict[str, Any], model_class) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate data using a Pydantic model
    
    Args:
        data: Data to validate
        model_class: Pydantic model class to use for validation
    
    Returns:
        Tuple of (is_valid, error_message, validation_details)
    """
    try:
        model_instance = model_class(**data)
        return True, None, None
    except ValidationError as e:
        error_details = {}
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            error_details[field] = error['msg']
        
        return False, "Validation failed", error_details
    except Exception as e:
        return False, f"Validation error: {str(e)}", None


def validate_external_resource(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate external resource data using Pydantic model
    
    Args:
        data: External resource data
    
    Returns:
        Tuple of (is_valid, error_message, validation_details)
    """
    return validate_with_pydantic_model(data, ExternalResource)


def validate_annotation_contributor(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate annotation contributor data using Pydantic model
    
    Args:
        data: Annotation contributor data
    
    Returns:
        Tuple of (is_valid, error_message, validation_details)
    """
    return validate_with_pydantic_model(data, AnnotationContributor)


def validate_moderator_approval(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate moderator approval data
    
    Args:
        data: Moderator approval data
    
    Returns:
        Tuple of (is_valid, error_message, validation_details)
    """
    required_fields = ['moderator_name', 'moderator_email']
    missing_fields = []
    
    for field in required_fields:
        if not data.get(field, '').strip():
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required moderator fields: {', '.join(missing_fields)}", {
            'missing_fields': missing_fields
        }
    
    # Validate moderator email
    is_valid, error = validate_email(data['moderator_email'])
    if not is_valid:
        return False, f"Invalid moderator email: {error}", None
    
    # Validate moderator ORCID if provided
    if data.get('moderator_identifier'):
        is_valid, error = validate_orcid(data['moderator_identifier'])
        if not is_valid:
            return False, f"Invalid moderator ORCID: {error}", None
    
    # Validate moderator URL if provided
    if data.get('moderator_url'):
        is_valid, error = validate_url(data['moderator_url'])
        if not is_valid:
            return False, f"Invalid moderator URL: {error}", None
    
    return True, None, None


def validate_user_registration(data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate user registration data
    
    Args:
        data: User registration data
    
    Returns:
        Tuple of (is_valid, error_message, validation_details)
    """
    required_fields = ['email', 'password']
    missing_fields = []
    
    for field in required_fields:
        if not data.get(field, '').strip():
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}", {
            'missing_fields': missing_fields
        }
    
    # Validate email format
    is_valid, error = validate_email(data['email'])
    if not is_valid:
        return False, error, None
    
    # Validate password strength (basic check)
    password = data['password']
    if len(password) < 6:
        return False, "Password must be at least 6 characters long", None
    
    # Check password confirmation if provided
    if 'confirm_password' in data:
        if data['password'] != data['confirm_password']:
            return False, "Passwords do not match", None
    
    return True, None, None


def validate_content_type(expected_type: str = 'application/json') -> Tuple[bool, Optional[str]]:
    """
    Validate request content type
    
    Args:
        expected_type: Expected content type
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    content_type = request.content_type
    if not content_type or not content_type.startswith(expected_type):
        return False, f"Content-Type must be {expected_type}"
    
    return True, None
