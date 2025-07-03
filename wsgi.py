#!/usr/bin/env python3.10
"""
WSGI configuration file - for PythonAnywhere deployment
Automotive Repair Management System
"""

import sys
import os

# Add project path to Python path
project_home = '/home/ChanMeng/automotive-repair-management-system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['DB_HOST'] = 'ChanMeng.mysql.pythonanywhere-services.com'
os.environ['DB_USER'] = 'ChanMeng'
os.environ['DB_NAME'] = 'ChanMeng$spb'

# Import Flask application
# Choose one import method:

# Method 1: Use refactored application factory pattern (recommended)
from app import create_app
application = create_app('production')

# Method 2: If using the old app.py file, comment out the above two lines and uncomment below
# from app import app as application

if __name__ == "__main__":
    application.run()
