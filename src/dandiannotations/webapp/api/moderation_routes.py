"""
API routes for moderation actions (approval, moderated views).
"""

import os
from flask import Blueprint, request

from .responses import (
    success_response,
    validation_error_response,
    not_found_response,
    unauthorized_response,
    forbidden_response,
)
from .decorators import handle_api_errors
from .validators import (
    validate_content_type,
    validate_json_request,
)
# Validation and serialization are handled in the service layer
from dandiannotations.webapp.repositories.resource_repository import ResourceRepository
from dandiannotations.webapp.services.resource_service import ResourceService
from dandiannotations.webapp.utils.auth import AuthManager


moderation_api_bp = Blueprint("moderation_api", __name__, url_prefix="/moderation")

# Create repository + service + auth instances aligned with other API modules
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "submissions")
resource_repository = ResourceRepository(SUBMISSIONS_DIR)
resource_service = ResourceService(resource_repository)

# Align config path with app.py (config/moderators.yaml)
MODERATORS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "moderators.yaml")
auth_manager = AuthManager(config_path=MODERATORS_CONFIG_PATH)


@moderation_api_bp.route("/submissions/<dandiset_id>/<resource_uuid>/<status>", methods=["GET"])
@handle_api_errors("Failed to retrieve resource")
def get_submission_by_status(dandiset_id, resource_uuid, status):
    """
    GET /api/moderation/submissions/{dandiset_id}/{resource_uuid}/{status}
    Thin route: auth check + delegate to service for validation and serialization.
    """
    # Check moderator privileges
    auth_error = auth_manager.require_moderator()
    if auth_error:
        if auth_error["status_code"] == 401:
            return unauthorized_response(auth_error["error"])
        else:
            return forbidden_response(auth_error["error"])

    # Validate status
    if status not in {"pending", "approved"}:
        return validation_error_response("Status parameter must be 'pending' or 'approved'")

    try:
        submission_filename = f"{resource_uuid}.yaml"
        submission = resource_service.get_submission_by_filename(dandiset_id, submission_filename, status)
        if not submission:
            return not_found_response("Submission")
        return success_response(data=submission, message="Submission retrieved successfully")
    except ValueError as e:
        return validation_error_response(str(e))
    except FileNotFoundError:
        return not_found_response("Submission")


@moderation_api_bp.route("/submissions/<status>", methods=["GET"])
@handle_api_errors("Failed to retrieve resources")
def get_submissions_by_status(status):
    """
    GET /api/moderation/submissions/{status}
    Get all resources across all dandisets by status (moderator only)
    """
    # Check moderator privileges
    auth_error = auth_manager.require_moderator()
    if auth_error:
        if auth_error["status_code"] == 401:
            return unauthorized_response(auth_error["error"])
        else:
            return forbidden_response(auth_error["error"])

    # Validate status
    if status not in {"pending", "approved"}:
        return validation_error_response("Status parameter must be 'pending' or 'approved'")

    # Pagination params
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    # Fetch data via service
    items, pagination = resource_service.get_all_resources(status, page=page, per_page=per_page)

    return success_response(
        data=items,
        message=f"{status.capitalize()} resources retrieved successfully",
        pagination=pagination
    )




@moderation_api_bp.route("/submissions/<dandiset_id>/<resource_uuid>/<status>", methods=["DELETE"])
@handle_api_errors("Failed to delete resource")
def delete_submission(dandiset_id, resource_uuid, status):
    """
    DELETE /api/moderation/submissions/{dandiset_id}/{resource_uuid}/{status}
    Thin route: auth + minimal HTTP checks; service handles validation and deletion.
    """
    # Check moderator privileges
    auth_error = auth_manager.require_moderator()
    if auth_error:
        if auth_error["status_code"] == 401:
            return unauthorized_response(auth_error["error"])
        else:
            return forbidden_response(auth_error["error"])

    # Validate status
    if status not in {"pending", "approved"}:
        return validation_error_response("Status parameter must be 'pending' or 'approved'")

    # Minimal HTTP checks (content type + JSON presence for moderator info)
    is_valid, error_msg = validate_content_type()
    if not is_valid:
        return validation_error_response(error_msg)
    is_valid, error_msg = validate_json_request()
    if not is_valid:
        return validation_error_response(error_msg)

    data = request.get_json() or {}
    try:
        submission_filename = f"{resource_uuid}.yaml"
        result = resource_service.delete_submission(dandiset_id, submission_filename, status, data)
        name = result.get("resource_name", resource_uuid)
        return success_response(data=result, message=f"Submission '{name}' deleted successfully")
    except ValueError as e:
        return validation_error_response(str(e))
    except FileNotFoundError:
        return not_found_response("Submission")


@moderation_api_bp.route("/submissions/<dandiset_id>/<resource_uuid>/approve", methods=["POST"])
@handle_api_errors("Failed to approve resource")
def approve_submission(dandiset_id, resource_uuid):
    """
    POST /api/moderation/submissions/{dandiset_id}/{resource_uuid}/approve
    Thin route: auth + minimal HTTP checks; service handles validation + serialization.
    """
    # Check moderator privileges
    auth_error = auth_manager.require_moderator()
    if auth_error:
        if auth_error["status_code"] == 401:
            return unauthorized_response(auth_error["error"])
        else:
            return forbidden_response(auth_error["error"])

    # Minimal HTTP checks (content type + JSON presence)
    is_valid, error_msg = validate_content_type()
    if not is_valid:
        return validation_error_response(error_msg)
    is_valid, error_msg = validate_json_request()
    if not is_valid:
        return validation_error_response(error_msg)

    data = request.get_json() or {}
    try:
        submission_filename = f"{resource_uuid}.yaml"
        approved = resource_service.approve_submission(dandiset_id, submission_filename, data)
        return success_response(data=approved, message="Submission approved successfully")
    except ValueError as e:
        return validation_error_response(str(e))
    except FileNotFoundError:
        return not_found_response("Submission")
