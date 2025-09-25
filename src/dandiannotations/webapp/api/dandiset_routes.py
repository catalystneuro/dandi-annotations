"""
Minimal API routes for per-dandiset resources.

Provides:
- GET /api/dandiset/<dandiset_id>/<status>  -> paginated list of resources by status
- GET /api/dandiset/<dandiset_id>/overview      -> per-dandiset statistics

Backed by ResourceService/ResourceRepository (new architecture).
"""
from flask import Blueprint, request
from .responses import success_response, unauthorized_response, forbidden_response, validation_error_response
from .decorators import handle_api_errors
import os

from dandiannotations.webapp.repositories.resource_repository import ResourceRepository
from dandiannotations.webapp.services.resource_service import ResourceService
from dandiannotations.webapp.utils.auth import AuthManager

dandiset_api_bp = Blueprint("dandiset_api", __name__, url_prefix="/dandiset")

# Repository + service instances
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "submissions")
resource_repository = ResourceRepository(SUBMISSIONS_DIR)
resource_service = ResourceService(resource_repository)

# Auth manager (moderators/users config)
MODERATORS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "moderators.yaml")
auth_manager = AuthManager(MODERATORS_CONFIG_PATH)


@dandiset_api_bp.route("/<dandiset_id>/<status>", methods=["GET"])
@handle_api_errors("Failed to retrieve resources")
def get_resources_by_dandiset(dandiset_id, status):
    """
    Return paginated resources for a dandiset and status.

    Path params:
      - dandiset_id (str)
      - status: 'pending' or 'approved'
    Query params:
      - page (int, optional, default=1)
      - per_page (int, optional, default=9)
    """
    # Validate status exactly
    if status not in {"pending", "approved"}:
        return validation_error_response("Status parameter must be 'pending' or 'approved'")

    # Enforce moderator privileges for pending
    if status == "pending":
        auth_error = auth_manager.require_moderator()
        if auth_error:
            if auth_error["status_code"] == 401:
                return unauthorized_response(auth_error["error"])
            else:
                return forbidden_response(auth_error["error"])

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=9, type=int)

    items, pagination = resource_service.get_resources_by_dandiset(dandiset_id, status, page=page, per_page=per_page)
    return success_response(
        data=items,
        pagination=pagination,
        message=f"{status.capitalize()} resources retrieved successfully."
    )


@dandiset_api_bp.route("/<dandiset_id>/overview", methods=["GET"])
@handle_api_errors("Failed to retrieve dandiset overview")
def get_dandiset_overview(dandiset_id):
    """
    Return per-dandiset statistics (approved_count, pending_count, totals, breakdowns).
    """
    stats = resource_service.get_dandiset_stats(dandiset_id)
    return success_response(data=stats, message="Dandiset overview retrieved successfully.")
