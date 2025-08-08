"""
Minimal API routes for the homepage.

Provides:
- GET /api/dandisets         -> paginated list of dandisets (accepts page, per_page)
- GET /api/dandisets/overview -> overview statistics (accepts include_community=true|false)

This is intentionally small and independent so you can start from scratch for the homepage API.
"""
from flask import Blueprint, request, jsonify
from typing import Tuple
from functools import wraps

from .responses import success_response
from .decorators import handle_api_errors
from dandiannotations.webapp.repositories.resource_repository import ResourceRepository
from dandiannotations.webapp.services.resource_service import ResourceService
from dandiannotations.webapp.utils.auth import AuthManager
import os

home_api_bp = Blueprint('home_api', __name__, url_prefix='/home')

# Create a repository + service instance using the same submissions dir as the app
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'submissions')
resource_repository = ResourceRepository(SUBMISSIONS_DIR)
resource_service = ResourceService(resource_repository)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
auth_manager = AuthManager(config_path=CONFIG_PATH)

@home_api_bp.route('/dandisets', methods=['GET'])
@handle_api_errors("Failed to retrieve dandisets")
def get_all_dandisets():
    """
    Return paginated dandisets.

    Query params:
    - page (int, optional, default=1)
    - per_page (int, optional, default=10)
    """
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)

    dandisets, pagination = resource_service.get_all_dandisets(page=page, per_page=per_page)
    response = success_response(data=dandisets, pagination=pagination, message="Dandisets retrieved successfully.")
    return response


@home_api_bp.route('/dandisets/overview', methods=['GET'])
@handle_api_errors("Failed to retrieve overview statistics")
def get_overview_stats():
    """
    Return overview statistics.

    If the user is a moderator, include community counts in the totals.
    """
    include_community = auth_manager.is_moderator()
    stats = resource_service.get_overview_stats(include_community=include_community)
    response = success_response(data=stats, message="Overview statistics retrieved successfully.")
    return response
