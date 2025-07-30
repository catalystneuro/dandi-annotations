"""
Authentication utilities for DANDI External Resources webapp
"""
import os
import yaml
import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash, request
from typing import Dict, Any, Optional
from pathlib import Path


class AuthManager:
    def __init__(self, config_path: str):
        """
        Initialize the authentication manager
        
        Args:
            config_path: Path to the moderators.yaml config file
        """
        self.config_path = Path(config_path)
        self._moderators = None
    
    def _load_moderators(self) -> Dict[str, Any]:
        """Load moderator credentials from YAML file"""
        if self._moderators is None:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
                    self._moderators = config.get('moderators', {})
            except FileNotFoundError:
                print(f"Warning: Moderators config file not found at {self.config_path}")
                self._moderators = {}
            except Exception as e:
                print(f"Error loading moderators config: {e}")
                self._moderators = {}
        
        return self._moderators
    
    def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verify username and password against stored credentials
        
        Args:
            username: The username to verify
            password: The plain text password to verify
            
        Returns:
            Moderator info dict if valid, None if invalid
        """
        moderators = self._load_moderators()
        
        if username not in moderators:
            return None
        
        moderator = moderators[username]
        stored_hash = moderator.get('password_hash', '').encode('utf-8')
        
        try:
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return {
                    'username': username,
                    'name': moderator.get('name', username),
                    'email': moderator.get('email', '')
                }
        except Exception as e:
            print(f"Error verifying password for {username}: {e}")
        
        return None
    
    def is_authenticated(self) -> bool:
        """Check if current session is authenticated"""
        return session.get('authenticated', False)
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user info"""
        if self.is_authenticated():
            return session.get('user_info')
        return None
    
    def login_user(self, user_info: Dict[str, Any]) -> None:
        """Log in a user by setting session variables"""
        session['authenticated'] = True
        session['user_info'] = user_info
        session.permanent = True  # Use permanent session (24 hours)
    
    def logout_user(self) -> None:
        """Log out the current user by clearing session"""
        session.pop('authenticated', None)
        session.pop('user_info', None)


def login_required(f):
    """
    Decorator to require authentication for a route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated', False):
            flash('You must be logged in to access this page.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def generate_password_hash(password: str) -> str:
    """
    Generate a bcrypt hash for a password
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hash string
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Utility function to create new moderator entries
def create_moderator_entry(username: str, password: str, name: str, email: str) -> Dict[str, Any]:
    """
    Create a new moderator entry with hashed password
    
    Args:
        username: Username for the moderator
        password: Plain text password
        name: Display name
        email: Email address
        
    Returns:
        Dictionary with moderator info including hashed password
    """
    return {
        'username': username,
        'password_hash': generate_password_hash(password),
        'name': name,
        'email': email
    }
