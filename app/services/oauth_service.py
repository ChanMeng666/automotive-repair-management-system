"""
OAuth Service
Direct Google OAuth integration for Flask applications
Since Neon Auth is designed for JavaScript frameworks, this provides
direct OAuth support for Flask/Jinja2 applications
"""
import os
import logging
from typing import Optional, Dict, Any, Tuple
from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for, session

logger = logging.getLogger(__name__)

# Global OAuth instance
oauth = OAuth()


def init_oauth(app: Flask) -> None:
    """
    Initialize OAuth with Flask app
    
    Configures Google OAuth using Neon's shared credentials for development
    or custom credentials for production
    """
    oauth.init_app(app)
    
    # Get OAuth credentials from environment
    google_client_id = app.config.get('GOOGLE_CLIENT_ID')
    google_client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
    
    # Only register Google if credentials are configured
    if google_client_id and google_client_secret:
        oauth.register(
            name='google',
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        logger.info("Google OAuth configured successfully")
    else:
        logger.warning("Google OAuth not configured - missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")


def get_google_oauth():
    """Get the Google OAuth client"""
    return oauth.create_client('google')


class OAuthService:
    """Service for handling OAuth authentication"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def is_google_configured(self) -> bool:
        """Check if Google OAuth is properly configured"""
        from flask import current_app
        return bool(
            current_app.config.get('GOOGLE_CLIENT_ID') and 
            current_app.config.get('GOOGLE_CLIENT_SECRET')
        )
    
    def create_or_update_user_from_google(self, user_info: Dict[str, Any]) -> Tuple[bool, Any, Optional[str]]:
        """
        Create or update a user from Google OAuth info
        
        Args:
            user_info: Google user info containing email, name, etc.
            
        Returns:
            Tuple of (success, user, error_message)
        """
        from app.models.user import User
        from app.extensions import db
        
        try:
            email = user_info.get('email')
            name = user_info.get('name', '')
            google_id = user_info.get('sub')  # Google's unique user ID
            picture = user_info.get('picture')
            
            if not email:
                return False, None, "Email not provided by Google"
            
            # Try to find existing user by email
            user = User.find_by_email(email)
            
            if user:
                # Update existing user with Google info if not set
                if not user.neon_auth_user_id:
                    user.neon_auth_user_id = f"google:{google_id}"
                    db.session.commit()
                self.logger.info(f"Existing user {email} signed in via Google")
            else:
                # Create new user
                username = email.split('@')[0]  # Use email prefix as username
                
                # Make username unique if needed
                base_username = username
                counter = 1
                while User.find_by_username(username):
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User(
                    username=username,
                    email=email,
                    neon_auth_user_id=f"google:{google_id}",
                    role='technician',  # Default role
                    is_active=True
                )
                # Set a random password for OAuth users (they won't use it)
                import secrets
                user.set_password(secrets.token_hex(32))
                
                db.session.add(user)
                db.session.commit()
                self.logger.info(f"New user {email} created via Google OAuth")
            
            return True, user, None
            
        except Exception as e:
            self.logger.error(f"Error creating/updating user from Google: {e}")
            db.session.rollback()
            return False, None, str(e)


# Global instance
oauth_service = OAuthService()
