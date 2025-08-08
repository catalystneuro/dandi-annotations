"""
Minimal API routes for the homepage.

Provides:
- GET /api/dandisets         -> paginated list of dandisets (accepts page, per_page)
- GET /api/dandisets/overview -> overview statistics (accepts include_community=true|false)

This is intentionally small and independent so you can start from scratch for the homepage API.
"""
from flask import Blueprint, request, jsonify
from typing import Tuple

from .responses import success_response, internal_error_response
from dandiannotations.webapp.repositories.resource_repository import ResourceRepository
from dandiannotations.webapp.services.resource_service import ResourceService
import os

home_api_bp = Blueprint('home_api', __name__, url_prefix='/home')

# Create a repository + service instance using the same submissions dir as the app
SUBMISSIONS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'submissions')
resource_repository = ResourceRepository(SUBMISSIONS_DIR)
resource_service = ResourceService(resource_repository)


@home_api_bp.route('/dandisets', methods=['GET'])
def get_all_dandisets():
    """
    Return paginated dandisets.

    Query params:
    - page (int, optional, default=1)
    - per_page (int, optional, default=10)
    """
    try:
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)

        dandisets, pagination = resource_service.get_all_dandisets(page=page, per_page=per_page)
        response = success_response(data=dandisets, pagination=pagination, message="Dandisets retrieved successfully.")
        return response
    except Exception as e:
        return internal_error_response(message=str(e))


@home_api_bp.route('/dandisets/overview', methods=['GET'])
def get_overview_stats():
    """
    Return overview statistics.

    Query params:
    - include_community (true|false) - whether to include community counts in totals.
    """
    try:
        include_community = request.args.get('include_community', 'false').lower() in ('1', 'true', 'yes')
        stats = resource_service.get_overview_stats(include_community=include_community)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
