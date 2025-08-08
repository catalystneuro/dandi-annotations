"""
API module for DANDI External Resources webapp
Provides REST API endpoints for programmatic access to all functionality
"""

from flask import Blueprint

# Create the API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes to register them with the blueprint
from . import routes
from . import home_routes
from . import submission_routes

# Register the sub-blueprints with the main API blueprint
api_bp.register_blueprint(home_routes.home_api_bp)
api_bp.register_blueprint(submission_routes.submission_api_bp)

__all__ = ['api_bp']
