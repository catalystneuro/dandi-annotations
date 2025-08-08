"""
API routes for resource submissions.

Provides:
- POST /api/submission -> create a new community submission
"""
from flask import Blueprint, request
from functools import wraps
import os

from .responses import created_response, validation_error_response, internal_error_response
from dandiannotations.webapp.repositories.resource_repository import ResourceRepository
from dandiannotations.webapp.services.resource_service import ResourceService

submission_api_bp = Blueprint('submission_api', __name__, url_prefix='/submission')

# Create a repository + service instance using the same submissions dir as the app
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'submissions')
resource_repository = ResourceRepository(SUBMISSIONS_DIR)
resource_service = ResourceService(resource_repository)


def handle_api_errors(error_message=None):
    """Decorator to handle API errors consistently"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValueError as e:
                # Validation errors
                return validation_error_response(str(e))
            except Exception as e:
                # General errors
                base_message = error_message or f"Error in {f.__name__.replace('_', ' ')}"
                return internal_error_response(f"{base_message}: {str(e)}")
        return decorated_function
    return decorator


@submission_api_bp.route('', methods=['POST'])
@handle_api_errors("Failed to submit resource")
def submit_resource():
    """
    Create a new community submission.
    
    Expects JSON payload with the form fields:
    - dandiset_id, resource_name, resource_url, repository, relation, resource_type
    - contributor_name, contributor_email
    - contributor_identifier (optional), contributor_url (optional)
    - resource_identifier (optional)
    
    Returns:
        201 Created with submission data and filename
    """
    # Validate content type
    if not request.is_json:
        return validation_error_response("Content-Type must be application/json")
    
    # Get JSON data
    try:
        form_data = request.get_json()
        if not form_data:
            return validation_error_response("Request body must contain JSON data")
    except Exception as e:
        return validation_error_response(f"Invalid JSON: {str(e)}")
    
    # Submit the resource via service layer - it returns properly formatted response data
    result = resource_service.submit_resource(form_data)
    location = f"/api/resources/{result['resource_id']}"

    return created_response(
        data=result,
        message="Resource submitted successfully.",
        location=location,
    )
