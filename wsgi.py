#!/usr/bin/env python3
"""
WSGI Configuration File
Platform-agnostic configuration for Railway, Heroku, and local development
Automotive Repair Management System
"""
import os
import sys

# Add project path to Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import Flask application using factory pattern
from app import create_app

# Create application instance
# Environment is determined by FLASK_ENV variable (defaults to 'production' for deployment)
application = create_app(os.environ.get('FLASK_ENV', 'production'))

# For compatibility with some WSGI servers that expect 'app'
app = application

if __name__ == "__main__":
    # For local development without gunicorn
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
