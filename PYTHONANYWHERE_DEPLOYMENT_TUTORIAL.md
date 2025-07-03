# Complete PythonAnywhere Deployment Tutorial
## Automotive Repair Management System

This comprehensive tutorial provides step-by-step instructions for deploying the Automotive Repair Management System to PythonAnywhere from scratch. It includes troubleshooting tips, common pitfalls, and best practices based on successful deployment experience.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-deployment Preparation](#pre-deployment-preparation)
3. [PythonAnywhere Account Setup](#pythonanywhere-account-setup)
4. [Code Deployment](#code-deployment)
5. [Database Configuration](#database-configuration)
6. [Python Environment Setup](#python-environment-setup)
7. [Web Application Configuration](#web-application-configuration)
8. [Testing and Troubleshooting](#testing-and-troubleshooting)
9. [Common Issues and Solutions](#common-issues-and-solutions)
10. [Security Considerations](#security-considerations)
11. [Maintenance and Updates](#maintenance-and-updates)

## 🎯 Prerequisites

Before starting the deployment process, ensure you have:

- A GitHub repository with your automotive repair management system
- A PythonAnywhere account (free or paid)
- Basic knowledge of command line operations
- Database schema file (`spb_local.sql`)
- Project requirements file (`requirements.txt`)

## 🔧 Pre-deployment Preparation

### 1. Prepare Configuration Files

Before uploading to PythonAnywhere, run the configuration update script locally:

```bash
python update_db_config.py
```

**Input required:**
- Your PythonAnywhere username
- Your MySQL database password (you'll set this on PythonAnywhere)

**What this script does:**
- Updates `connect.py` with your PythonAnywhere database credentials
- Updates `wsgi.py` with your specific project paths
- Prepares configuration for production environment

### 2. Verify Project Structure

Ensure your project contains these essential files:
```
automotive-repair-management-system/
├── app/                           # Modern Flask application structure
├── app.py                         # Legacy Flask application (fallback)
├── wsgi.py                        # WSGI configuration
├── connect.py                     # Database connection config
├── requirements.txt               # Python dependencies
├── spb_local.sql                 # Database schema
├── config/                        # Configuration files
└── static/                        # Static assets
```

## 🌐 PythonAnywhere Account Setup

### 1. Create Account

1. Visit [PythonAnywhere.com](https://www.pythonanywhere.com/)
2. Sign up for an account (free accounts have limitations but work for testing)
3. Note your username - you'll need it throughout the deployment

### 2. Account Limitations (Free Tier)

Be aware of free account limitations:
- One web app
- Limited CPU seconds per day
- 512MB disk space
- One MySQL database
- HTTPS only on pythonanywhere.com subdomains

## 📁 Code Deployment

### Method 1: Git Clone (Recommended)

1. Open a **Bash console** in PythonAnywhere
2. Clone your repository:
```bash
cd ~
git clone https://github.com/yourusername/automotive-repair-management-system.git
cd automotive-repair-management-system
```

### Method 2: File Upload

If Git clone fails:
1. Go to **Files** tab in PythonAnywhere dashboard
2. Create directory: `/home/yourusername/automotive-repair-management-system/`
3. Upload all project files manually
4. Maintain the directory structure

## 🗄️ Database Configuration

### 1. Create MySQL Database

1. Go to **Databases** tab in PythonAnywhere dashboard
2. If first time: Set your MySQL password
3. Create a new database named: `yourusername$spb`
   - **Important:** The format must be `username$databasename`
   - Example: If username is "johnsmith", database name is "johnsmith$spb"

### 2. Import Database Schema

**Option A: Using MySQL Console (Recommended)**
1. In Databases tab, click **Open MySQL console**
2. Select your database: `yourusername$spb`
3. Copy and paste the entire contents of `spb_local.sql`
4. Execute the SQL commands

**Option B: Using Command Line**
```bash
mysql -u yourusername -p'your_password' -h yourusername.mysql.pythonanywhere-services.com yourusername\$spb < spb_local.sql
```

### 3. Verify Database Import

Check that tables were created:
```sql
SHOW TABLES;
DESCRIBE customer;
DESCRIBE job;
```

You should see tables: `customer`, `job`, `service`, `part`, `job_service`, `job_part`

## 🐍 Python Environment Setup

### 1. Create Virtual Environment

In the Bash console:
```bash
cd ~/automotive-repair-management-system
python3.10 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Test Python Imports

Verify critical modules work:
```bash
python3.10 -c "import mysql.connector; print('MySQL connector OK')"
python3.10 -c "from app import create_app; print('Flask app import OK')"
```

## 🌐 Web Application Configuration

### 1. Create Web App

1. Go to **Web** tab in PythonAnywhere dashboard
2. Click **Add a new web app**
3. Choose your domain: `yourusername.pythonanywhere.com`
4. Select **Manual configuration**
5. Choose **Python 3.10**

### 2. Configure WSGI File

1. In Web tab, find **Code** section
2. Click on WSGI configuration file link
3. **Delete all existing content**
4. Replace with your `wsgi.py` content:

```python
#!/usr/bin/env python3.10
"""
WSGI Configuration for Automotive Repair Management System
"""

import sys
import os

# Add project path to Python path
project_home = '/home/yourusername/automotive-repair-management-system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['DB_HOST'] = 'yourusername.mysql.pythonanywhere-services.com'
os.environ['DB_USER'] = 'yourusername'
os.environ['DB_NAME'] = 'yourusername$spb'

# Import Flask application
from app import create_app
application = create_app('production')

# Fallback to legacy app.py if needed
# from app import app as application

if __name__ == "__main__":
    application.run()
```

**Replace `yourusername` with your actual PythonAnywhere username**

### 3. Set Virtual Environment

In Web tab, **Virtualenv** section:
```
/home/yourusername/automotive-repair-management-system/venv
```

### 4. Configure Static Files

In **Static files** section:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/automotive-repair-management-system/app/static/` |

### 5. Set Environment Variables (Optional)

In WSGI file or through PythonAnywhere, set:
```python
os.environ['SECRET_KEY'] = 'your-production-secret-key'
os.environ['DB_PASSWORD'] = 'your_mysql_password'
```

## 🧪 Testing and Troubleshooting

### 1. Reload Web App

1. In Web tab, click **Reload** button
2. Wait for reload to complete

### 2. Test Application

1. Visit: `https://yourusername.pythonanywhere.com`
2. Check if application loads without errors

### 3. Check Error Logs

If application doesn't work:
1. In Web tab, click **Error log**
2. Review recent errors
3. Common issues are listed below

## 🚨 Common Issues and Solutions

### Issue 1: ImportError - No module named 'app'

**Symptoms:** 500 error, "No module named 'app'" in error log

**Solutions:**
- Verify project path in WSGI file is correct
- Check that `app/` directory exists in project
- Ensure virtual environment is set correctly
- Try fallback to legacy `app.py`:
```python
# Comment out:
# from app import create_app
# application = create_app('production')

# Uncomment:
from app import app as application
```

### Issue 2: Database Connection Errors

**Symptoms:** "Access denied for user", "Unknown database"

**Solutions:**
- Verify database name format: `username$spb`
- Check database password in `connect.py`
- Confirm database exists in PythonAnywhere Databases tab
- Test connection manually:
```python
import mysql.connector
conn = mysql.connector.connect(
    host='yourusername.mysql.pythonanywhere-services.com',
    user='yourusername',
    password='your_password',
    database='yourusername$spb'
)
print("Database connection OK")
```

### Issue 3: Static Files Not Loading

**Symptoms:** CSS/JS files return 404 errors

**Solutions:**
- Verify static files path in Web tab configuration
- Check that `app/static/` directory contains CSS/JS files
- Ensure static URL mapping is `/static/` → `/home/username/project/app/static/`

### Issue 4: ModuleNotFoundError for Dependencies

**Symptoms:** "No module named 'mysql'" or similar

**Solutions:**
- Ensure virtual environment is activated during pip install
- Verify `requirements.txt` contains all dependencies
- Reinstall requirements:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue 5: Application Structure Issues

**Symptoms:** Various import errors, application won't start

**Solutions:**
- The project supports both modern (app/) and legacy (app.py) structures
- If modern structure fails, try legacy mode in WSGI file
- Ensure all necessary files are uploaded

## 🔒 Security Considerations

### 1. Production Secret Key

Update secret key in production:
```python
os.environ['SECRET_KEY'] = 'your-very-secure-random-key-here'
```

### 2. Database Security

- Use strong MySQL password
- Never commit passwords to version control
- Use environment variables for sensitive data

### 3. HTTPS Configuration

PythonAnywhere provides HTTPS by default for `.pythonanywhere.com` domains

## 🔄 Maintenance and Updates

### 1. Updating Code

To update your application:
```bash
cd ~/automotive-repair-management-system
git pull origin main
# If virtual environment packages changed:
source venv/bin/activate
pip install -r requirements.txt
```

Then reload web app in PythonAnywhere Web tab.

### 2. Database Updates

For database schema changes:
1. Create migration SQL scripts
2. Test in development first
3. Apply to production database via MySQL console

### 3. Monitoring

- Regularly check error logs
- Monitor CPU usage (especially on free accounts)
- Set up log rotation for long-term deployments

## 📊 Deployment Automation

### Using the Deployment Script

The project includes `deploy_to_pythonanywhere.sh` for automation:

```bash
export PA_USERNAME=yourusername
bash deploy_to_pythonanywhere.sh
```

This script:
- Creates virtual environment
- Installs dependencies
- Tests imports
- Provides configuration reminders

## 🎉 Success Checklist

Your deployment is successful when:

- [ ] Application loads at `https://yourusername.pythonanywhere.com`
- [ ] Database connection works (no DB errors)
- [ ] Static files load correctly (CSS styling visible)
- [ ] Application functions work (can navigate pages)
- [ ] No errors in PythonAnywhere error log

## 📞 Getting Help

If you encounter issues:

1. Check PythonAnywhere error logs first
2. Review this tutorial's troubleshooting section
3. Consult [PythonAnywhere help documentation](https://help.pythonanywhere.com/)
4. Check Flask deployment guides
5. Review project's GitHub issues

## 📝 Summary

This tutorial provides a complete deployment workflow that has been tested and verified. The key success factors are:

1. **Proper file preparation** before upload
2. **Correct database configuration** with proper naming
3. **Virtual environment setup** with all dependencies
4. **Accurate WSGI configuration** with correct paths
5. **Systematic troubleshooting** when issues arise

Following this guide should result in a successful deployment of your automotive repair management system to PythonAnywhere.

---

**Last Updated:** $(date)
**Tested Environment:** PythonAnywhere Free/Paid Accounts, Python 3.10, Flask 3.0.1
**Project Version:** Compatible with both modern (app/) and legacy (app.py) structures 