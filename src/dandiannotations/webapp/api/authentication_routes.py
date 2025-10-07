"""
Authentication API routes (login, logout, register).
"""

import os
from flask import Blueprint, request

from .responses import (
    success_response,
    error_response,
    validation_error_response,
    created_response,
)
from .decorators import handle_api_errors
from dandiannotations.webapp.utils.auth import AuthManager

auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/auth")

# Align config path with app.py (config/moderators.yaml)
MODERATORS_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "moderators.yaml")
auth_manager = AuthManager(config_path=MODERATORS_CONFIG_PATH)

from typing import Any, Dict
def serialize_user_info(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize user information for API response (excluding sensitive data)
    
    Args:
        user_data: User data dictionary
    
    Returns:
        Serialized user data (without password)
    """
    if not user_data:
        return None
    
    # Create a copy and remove sensitive fields
    serialized = user_data.copy()
    
    # Remove password and other sensitive fields
    sensitive_fields = ['password', 'password_hash', 'salt']
    for field in sensitive_fields:
        serialized.pop(field, None)
    
    return serialized


@auth_api_bp.route("/login", methods=["POST"])
@handle_api_errors("Failed to log in")
def login():
    """
    POST /api/auth/login
    Authenticate user and create session (auto-login on success).
    Body: { "username": "<email or moderator username>", "password": "<string>" }
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return validation_error_response("Username and password are required")

    user_info = auth_manager.verify_credentials(username, password)
    if not user_info:
        return error_response("Invalid username or password", "INVALID_CREDENTIALS", 401)

    # Auto-login
    auth_manager.login_user(user_info)
    serialized = serialize_user_info(user_info)
    return success_response(
        data=serialized,
        message="Login successful"
    )


@auth_api_bp.route("/logout", methods=["POST"])
@handle_api_errors("Failed to log out")
def logout():
    """
    POST /api/auth/logout
    Logout current user.
    """
    user_info = auth_manager.get_current_user()
    auth_manager.logout_user()

    message = "Logout successful"
    if user_info:
        message = f"Logout successful for {user_info.get('name', user_info.get('username', 'user'))}"

    return success_response(
        data=None,
        message=message
    )


@auth_api_bp.route("/register", methods=["POST"])
@handle_api_errors("Failed to register")
def register():
    """
    POST /api/auth/register
    Register a new user (auto-login on success).
    Body: { "email": "<string>", "password": "<string>", "confirm_password": "<string>" }
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    confirm_password = (data.get("confirm_password") or "").strip()

    if not email or not password:
        return validation_error_response("Email and password are required")
    if password != confirm_password:
        return validation_error_response("Passwords do not match")

    # Attempt to register
    if not auth_manager.register_user(email, password):
        return error_response("Email already exists", "EMAIL_EXISTS", 409)

    # Auto-login after registration
    user_info = auth_manager.verify_credentials(email, password)
    if user_info:
        auth_manager.login_user(user_info)
        serialized = serialize_user_info(user_info)
        return created_response(
            data=serialized,
            message="Registration successful"
        )
    else:
        # Fallback: registration ok, login failed (unexpected)
        return success_response(
            data=None,
            message="Registration successful. Please log in."
        )
