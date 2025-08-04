"""
Standardized API response helpers for consistent JSON responses
"""

from flask import jsonify
from typing import Any, Dict, Optional, Union
import traceback


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200,
    pagination: Optional[Dict[str, Any]] = None
) -> tuple:
    """
    Create a standardized success response
    
    Args:
        data: The response data
        message: Optional success message
        status_code: HTTP status code (default: 200)
        pagination: Optional pagination metadata
    
    Returns:
        Tuple of (response, status_code)
    """
    response_data = {
        "success": True,
        "data": data
    }
    
    if message:
        response_data["message"] = message
    
    if pagination:
        response_data["pagination"] = pagination
    
    return jsonify(response_data), status_code


def error_response(
    message: str,
    error_code: str = "GENERAL_ERROR",
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> tuple:
    """
    Create a standardized error response
    
    Args:
        message: Human-readable error message
        error_code: Machine-readable error code
        status_code: HTTP status code (default: 400)
        details: Optional detailed error information
    
    Returns:
        Tuple of (response, status_code)
    """
    response_data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        }
    }
    
    if details:
        response_data["error"]["details"] = details
    
    return jsonify(response_data), status_code


def validation_error_response(
    validation_errors: Union[str, Dict[str, Any], list],
    status_code: int = 422
) -> tuple:
    """
    Create a validation error response
    
    Args:
        validation_errors: Validation error details
        status_code: HTTP status code (default: 422)
    
    Returns:
        Tuple of (response, status_code)
    """
    if isinstance(validation_errors, str):
        details = {"general": validation_errors}
    elif isinstance(validation_errors, list):
        details = {"errors": validation_errors}
    else:
        details = validation_errors
    
    return error_response(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        status_code=status_code,
        details=details
    )


def not_found_response(resource: str = "Resource") -> tuple:
    """
    Create a not found error response
    
    Args:
        resource: Name of the resource that wasn't found
    
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        message=f"{resource} not found",
        error_code="NOT_FOUND",
        status_code=404
    )


def unauthorized_response(message: str = "Authentication required") -> tuple:
    """
    Create an unauthorized error response
    
    Args:
        message: Custom unauthorized message
    
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        message=message,
        error_code="UNAUTHORIZED",
        status_code=401
    )


def forbidden_response(message: str = "Access denied") -> tuple:
    """
    Create a forbidden error response
    
    Args:
        message: Custom forbidden message
    
    Returns:
        Tuple of (response, status_code)
    """
    return error_response(
        message=message,
        error_code="FORBIDDEN",
        status_code=403
    )


def internal_error_response(
    message: str = "Internal server error",
    include_traceback: bool = False
) -> tuple:
    """
    Create an internal server error response
    
    Args:
        message: Custom error message
        include_traceback: Whether to include traceback in response (for debugging)
    
    Returns:
        Tuple of (response, status_code)
    """
    details = None
    if include_traceback:
        details = {"traceback": traceback.format_exc()}
    
    return error_response(
        message=message,
        error_code="INTERNAL_ERROR",
        status_code=500,
        details=details
    )


def created_response(
    data: Any = None,
    message: str = "Resource created successfully",
    location: Optional[str] = None
) -> tuple:
    """
    Create a resource created response
    
    Args:
        data: The created resource data
        message: Success message
        location: Optional location header value
    
    Returns:
        Tuple of (response, status_code)
    """
    response, status_code = success_response(
        data=data,
        message=message,
        status_code=201
    )
    
    if location:
        response.headers['Location'] = location
    
    return response, status_code


def paginated_response(
    data: list,
    page: int,
    per_page: int,
    total_items: int,
    message: Optional[str] = None
) -> tuple:
    """
    Create a paginated response with metadata
    
    Args:
        data: List of items for current page
        page: Current page number
        per_page: Items per page
        total_items: Total number of items
        message: Optional success message
    
    Returns:
        Tuple of (response, status_code)
    """
    import math
    
    total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
    has_prev = page > 1
    has_next = page < total_pages
    
    pagination = {
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next,
        "prev_page": page - 1 if has_prev else None,
        "next_page": page + 1 if has_next else None,
        "start_item": (page - 1) * per_page + 1 if total_items > 0 else 0,
        "end_item": min(page * per_page, total_items)
    }
    
    return success_response(
        data=data,
        message=message,
        pagination=pagination
    )
