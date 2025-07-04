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
os.environ['DB_NAME'] = 'ChanMeng$automotive-repair-management-system'
os.environ['DB_PASSWORD'] = '1160210Mc'

# Import Flask application using factory pattern
from app import create_app
application = create_app('production')

if __name__ == "__main__":
    application.run()
