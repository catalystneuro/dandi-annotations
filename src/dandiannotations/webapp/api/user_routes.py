"""
User submissions API routes (current user's submissions).
"""

import os
from flask import Blueprint, request

from .responses import (
    success_response,
    unauthorized_response,
    forbidden_response,
    validation_error_response,
)
from .decorators import handle_api_errors
from dandiannotations.webapp.services.resource_service import ResourceService
from dandiannotations.webapp.repositories.resource_repository import ResourceRepository
from dandiannotations.webapp.utils.auth import AuthManager

user_api_bp = Blueprint("user_api", __name__, url_prefix="/resources")

# Reuse the same storage/config as other API modules
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "submissions")
resource_repository = ResourceRepository(SUBMISSIONS_DIR)
resource_service = ResourceService(resource_repository)

MODERATORS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "moderators.yaml")
auth_manager = AuthManager(config_path=MODERATORS_CONFIG_PATH)


@user_api_bp.route("/user/<user_email>/<status>", methods=["GET"])
@handle_api_errors("Failed to retrieve user submissions")
def get_user_submissions_by_status(user_email, status):
    """
    GET /api/resources/user/{user_email}/{status}
    Return the current user's submissions by status (authentication required).
    Users can only view their own submissions.
    Path params:
      - status: 'pending' or 'approved'
    Query params:
      - page (int, default 1)
      - per_page (int, default 10)
    """
    # Require authentication
    auth_error = auth_manager.require_authentication()
    if auth_error:
        return unauthorized_response(auth_error["error"])

    current_user = auth_manager.get_current_user()
    if not current_user or current_user.get("email") != user_email:
        return forbidden_response("You can only view your own submissions")

    # Validate status exactly
    if status not in {"pending", "approved"}:
        return validation_error_response("Status parameter must be 'pending' or 'approved'")

    # Parse pagination params
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=10, type=int)

    # Basic bounds checks
    if page < 1 or per_page < 1:
        return validation_error_response("Pagination parameters must be >= 1")

    items, pagination = resource_service.get_resources_by_user(
        user_email=user_email,
        status=status,
        page=page,
        per_page=per_page,
    )

    return success_response(
        data=items,
        pagination=pagination,
        message=f"User {status} submissions retrieved successfully",
    )
