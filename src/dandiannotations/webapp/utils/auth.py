"""
Authentication utilities for DANDI External Resources webapp
"""
import os
import yaml
import bcrypt
from datetime import datetime
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
        self.users_config_path = self.config_path.parent / "users.yaml"
        self._moderators = None
        self._users = None
    
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
    
    def _load_users(self) -> Dict[str, Any]:
        """Load user credentials from YAML file"""
        if self._users is None:
            try:
                with open(self.users_config_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
                    self._users = config.get('users', {}) if config else {}
            except FileNotFoundError:
                # Create empty users file if it doesn't exist
                self._users = {}
                self._save_users()
            except Exception as e:
                print(f"Error loading users config: {e}")
                self._users = {}
        
        return self._users
    
    def _save_users(self) -> None:
        """Save users to YAML file"""
        try:
            # Ensure the directory exists
            self.users_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.users_config_path, 'w', encoding='utf-8') as file:
                yaml.dump({'users': self._users}, file, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
        except Exception as e:
            print(f"Error saving users config: {e}")
    
    def verify_credentials(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Verify username and password against stored credentials (both moderators and users)
        
        Args:
            username: The username (email) to verify
            password: The plain text password to verify
            
        Returns:
            User info dict with user_type if valid, None if invalid
        """
        # First check moderators
        moderators = self._load_moderators()
        if username in moderators:
            moderator = moderators[username]
            stored_hash = moderator.get('password_hash', '').encode('utf-8')
            
            try:
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return {
                        'username': username,
                        'name': moderator.get('name', username),
                        'email': moderator.get('email', username),
                        'user_type': 'moderator'
                    }
            except Exception as e:
                print(f"Error verifying moderator password for {username}: {e}")
        
        # Then check regular users
        users = self._load_users()
        if username in users:
            user = users[username]
            stored_hash = user.get('password_hash', '').encode('utf-8')
            
            try:
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return {
                        'username': username,
                        'name': user.get('name', username),
                        'email': username,  # username is email for regular users
                        'user_type': 'user'
                    }
            except Exception as e:
                print(f"Error verifying user password for {username}: {e}")
        
        return None
    
    def register_user(self, email: str, password: str) -> bool:
        """
        Register a new user
        
        Args:
            email: User's email address (used as username)
            password: Plain text password
            
        Returns:
            True if successful, False if user already exists
        """
        users = self._load_users()
        moderators = self._load_moderators()
        
        # Check if email already exists in either users or moderators
        if email in users or email in moderators:
            return False
        
        # Add new user
        users[email] = {
            'password_hash': generate_password_hash(password),
            'name': email.split('@')[0],  # Use part before @ as default name
            'registration_date': datetime.now().isoformat()
        }
        
        self._users = users
        self._save_users()
        return True
    
    def is_moderator(self) -> bool:
        """Check if current user is a moderator"""
        user_info = self.get_current_user()
        return user_info and user_info.get('user_type') == 'moderator'
    
    def get_user_type(self) -> Optional[str]:
        """Get the type of the current user ('moderator', 'user', or None)"""
        user_info = self.get_current_user()
        return user_info.get('user_type') if user_info else None
    
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
