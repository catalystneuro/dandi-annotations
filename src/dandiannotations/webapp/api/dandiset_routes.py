"""
Minimal API routes for per-dandiset resources.

Provides:
- GET /api/dandiset/<dandiset_id>/approved   -> paginated list of approved resources
- GET /api/dandiset/<dandiset_id>/community  -> paginated list of community (pending) resources (moderator only)
- GET /api/dandiset/<dandiset_id>/overview  -> per-dandiset statistics

Backed by ResourceService/ResourceRepository (new architecture).
"""
from flask import Blueprint, request
from .responses import success_response, unauthorized_response, forbidden_response
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


@dandiset_api_bp.route("/<dandiset_id>/approved", methods=["GET"])
@handle_api_errors("Failed to retrieve approved resources")
def get_approved_resources(dandiset_id):
    """
    Return paginated approved resources for a dandiset.

    Query params:
    - page (int, optional, default=1)
    - per_page (int, optional, default=9)
    """
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=9, type=int)

    items, pagination = resource_service.get_resources_by_dandiset(dandiset_id, 'approved', page=page, per_page=per_page)
    return success_response(data=items, pagination=pagination, message="Approved resources retrieved successfully.")


@dandiset_api_bp.route("/<dandiset_id>/community", methods=["GET"])
@handle_api_errors("Failed to retrieve community resources")
def get_community_resources(dandiset_id):
    """
    Return paginated community (pending) resources for a dandiset.

    Auth:
      - Moderator only
    Query params:
      - page (int, optional, default=1)
      - per_page (int, optional, default=9)
    """
    # Enforce moderator privileges
    auth_error = auth_manager.require_moderator()
    if auth_error:
        if auth_error["status_code"] == 401:
            return unauthorized_response(auth_error["error"])
        else:
            return forbidden_response(auth_error["error"])

    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=9, type=int)

    items, pagination = resource_service.get_resources_by_dandiset(dandiset_id, 'community', page=page, per_page=per_page)
    return success_response(data=items, pagination=pagination, message="Community resources retrieved successfully.")


@dandiset_api_bp.route("/<dandiset_id>/overview", methods=["GET"])
@handle_api_errors("Failed to retrieve dandiset overview")
def get_dandiset_overview(dandiset_id):
    """
    Return per-dandiset statistics (approved_count, pending_count, totals, breakdowns).
    """
    stats = resource_service.get_dandiset_stats(dandiset_id)
    return success_response(data=stats, message="Dandiset overview retrieved successfully.")
