#!/usr/bin/env python3
"""
Database configuration update script
Used to update database connection configuration for PythonAnywhere deployment
"""

import os
import sys


def update_connect_py(username, password):
    """Update database configuration in connect.py file"""
    
    connect_content = f'''# Database configuration for PythonAnywhere
# This file is used for compatibility with database connections in the old app.py file

# PythonAnywhere MySQL database configuration
dbhost = '{username}.mysql.pythonanywhere-services.com'
dbuser = '{username}'
dbpass = '{password}'
dbname = '{username}$spb'

# Note:
# 1. dbhost format: username.mysql.pythonanywhere-services.com
# 2. dbname format: username$spb
# 3. dbuser is your PythonAnywhere username
# 4. dbpass is the password you set on the PythonAnywhere database page
'''
    
    try:
        with open('connect.py', 'w', encoding='utf-8') as f:
            f.write(connect_content)
        print(f"✅ connect.py configuration updated")
        print(f"   Database host: {username}.mysql.pythonanywhere-services.com")
        print(f"   Database user: {username}")
        print(f"   Database name: {username}$spb")
        return True
    except Exception as e:
        print(f"❌ Failed to update connect.py: {e}")
        return False


def update_wsgi_py(username):
    """Update project path in wsgi.py file"""
    
    wsgi_content = f'''#!/usr/bin/env python3.10
"""
WSGI configuration file - for PythonAnywhere deployment
Automotive Repair Management System
"""

import sys
import os

# Add project path to Python path
project_home = '/home/{username}/automotive-repair-management-system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['DB_HOST'] = '{username}.mysql.pythonanywhere-services.com'
os.environ['DB_USER'] = '{username}'
os.environ['DB_NAME'] = '{username}$spb'

# Import Flask application
# Choose one import method:

# Method 1: Use refactored application factory pattern (recommended)
from app import create_app
application = create_app('production')

# Method 2: If using the old app.py file, comment out the above two lines and uncomment below
# from app import app as application

if __name__ == "__main__":
    application.run()
'''
    
    try:
        with open('wsgi.py', 'w', encoding='utf-8') as f:
            f.write(wsgi_content)
        print(f"✅ wsgi.py configuration updated")
        print(f"   Project path: /home/{username}/automotive-repair-management-system")
        return True
    except Exception as e:
        print(f"❌ Failed to update wsgi.py: {e}")
        return False


def main():
    """Main function"""
    print("🔧 PythonAnywhere Database Configuration Update Tool")
    print("=" * 50)
    
    # Get user input
    username = input("Please enter your PythonAnywhere username: ").strip()
    if not username:
        print("❌ Username cannot be empty")
        sys.exit(1)
    
    password = input("Please enter your MySQL database password: ").strip()
    if not password:
        print("❌ Password cannot be empty")
        sys.exit(1)
    
    print(f"\n📝 Configuration information:")
    print(f"   Username: {username}")
    print(f"   Database: {username}$spb")
    print(f"   Host: {username}.mysql.pythonanywhere-services.com")
    
    confirm = input("\nConfirm configuration update? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Update cancelled")
        sys.exit(0)
    
    print("\n🔄 Starting configuration file update...")
    
    # Update configuration files
    success = True
    success &= update_connect_py(username, password)
    success &= update_wsgi_py(username)
    
    if success:
        print("\n🎉 Configuration update completed!")
        print("\n📋 Next steps:")
        print("1. Upload project code to PythonAnywhere")
        print("2. Create database on PythonAnywhere")
        print("3. Import database schema (spb_local.sql)")
        print("4. Configure web application")
        print("5. Copy wsgi.py content to PythonAnywhere WSGI configuration file")
        print("\n📚 For detailed steps, refer to PYTHONANYWHERE_DEPLOYMENT_GUIDE.md")
    else:
        print("\n❌ Configuration update failed, please check error messages")
        sys.exit(1)


if __name__ == "__main__":
    main() 