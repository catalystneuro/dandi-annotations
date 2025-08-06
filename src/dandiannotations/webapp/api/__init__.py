"""
API module for DANDI External Resources webapp
Provides REST API endpoints for programmatic access to all functionality
"""

from flask import Blueprint

# Create the API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes to register them with the blueprint
from . import routes

__all__ = ['api_bp']
