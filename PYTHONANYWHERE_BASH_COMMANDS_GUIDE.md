# PythonAnywhere Bash Console Deployment Commands Guide

## Complete Command Reference for Deploying Automotive Repair Management System

This guide provides all the bash console commands needed to deploy the automotive repair management system to PythonAnywhere from scratch. Follow these commands in order.

## Prerequisites

- PythonAnywhere account (free or paid)
- GitHub repository with the project code
- Basic familiarity with command line operations

---

## Step 1: Initial Setup and Code Download

### 1.1 Navigate to Home Directory
```bash
cd ~
```

### 1.2 Clone the Project Repository
```bash
git clone https://github.com/ChanMeng666/automotive-repair-management-system.git
```

### 1.3 Enter Project Directory
```bash
cd automotive-repair-management-system
```

### 1.4 Check Project Structure
```bash
ls -la
```

---

## Step 2: Python Virtual Environment Setup

### 2.1 Create Virtual Environment
```bash
python3.10 -m venv venv
```

### 2.2 Activate Virtual Environment
```bash
source venv/bin/activate
```

### 2.3 Verify Virtual Environment
```bash
which python
which pip
```

---

## Step 3: Dependencies Installation

### 3.1 Upgrade pip
```bash
pip install --upgrade pip
```

### 3.2 Install Project Dependencies
```bash
pip install -r requirements.txt
```

### 3.3 Verify Installations
```bash
pip list
```

### 3.4 Check Flask Installation
```bash
python -c "import flask; print(f'Flask version: {flask.__version__}')"
```

---

## Step 4: Database Setup Commands

### 4.1 Check if MySQL Client is Available
```bash
which mysql
```

### 4.2 Test Database Connection (replace with your credentials)
```bash
mysql -u your_username -p -h your_username.mysql.pythonanywhere-services.com
```

### 4.3 Create Database (inside MySQL prompt)
```sql
CREATE DATABASE your_username$spb;
USE your_username$spb;
SOURCE spb_local.sql;
SHOW TABLES;
SELECT COUNT(*) FROM customers;
EXIT;
```

### 4.4 Test Database Connection from Python
```bash
python -c "
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='your_username.mysql.pythonanywhere-services.com',
        user='your_username',
        password='your_password',
        database='your_username\$spb',
        pool_size=1
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM customers')
    count = cursor.fetchone()[0]
    print(f'Database connected successfully. Customer count: {count}')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

---

## Step 5: Configuration and Testing

### 5.1 Run Database Configuration Script
```bash
python update_db_config.py
```

### 5.2 Make Deployment Script Executable
```bash
chmod +x deploy_to_pythonanywhere.sh
```

### 5.3 Run Deployment Script
```bash
./deploy_to_pythonanywhere.sh
```

### 5.4 Test Application Imports
```bash
python -c "
try:
    from app import app
    print('App imported successfully')
except Exception as e:
    print(f'App import failed: {e}')
"
```

---

## Step 6: WSGI Configuration

### 6.1 Check WSGI File
```bash
cat wsgi.py
```

### 6.2 Test WSGI Application
```bash
python -c "
try:
    from wsgi import application
    print('WSGI application loaded successfully')
except Exception as e:
    print(f'WSGI failed: {e}')
"
```

### 6.3 Check for Alternative WSGI Files
```bash
ls -la wsgi*.py
```

---

## Step 7: File Permissions and Structure Verification

### 7.1 Set Proper Permissions
```bash
chmod 644 *.py
chmod 755 .
```

### 7.2 Check Static Files
```bash
ls -la app/static/
ls -la app/static/css/
ls -la app/static/js/
```

### 7.3 Check Templates
```bash
ls -la app/templates/
ls -la templates/
```

---

## Step 8: Environment Variables and Configuration

### 8.1 Check Environment Variables
```bash
printenv | grep -i flask
printenv | grep -i python
```

### 8.2 Set Environment Variables (if needed)
```bash
export FLASK_APP=app.py
export FLASK_ENV=production
```

### 8.3 Check Python Path
```bash
python -c "import sys; print('\n'.join(sys.path))"
```

---

## Step 9: Final Testing Commands

### 9.1 Test Database Connection
```bash
python -c "
import mysql.connector
from config.base import Config
try:
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        pool_size=1
    )
    print('Database configuration is correct')
    conn.close()
except Exception as e:
    print(f'Database configuration error: {e}')
"
```

### 9.2 Test Flask Application
```bash
python -c "
try:
    import app
    print('Flask app module imported successfully')
    if hasattr(app, 'app'):
        print('Flask app instance found')
    else:
        print('Flask app instance not found')
except Exception as e:
    print(f'Flask app test failed: {e}')
"
```

### 9.3 Check for Template Files
```bash
find . -name "*.html" -type f | head -10
```

---

## Step 10: Troubleshooting Commands

### 10.1 Check Log Files
```bash
ls -la logs/
tail -f logs/error.log  # if log files exist
```

### 10.2 Check for Missing Dependencies
```bash
python -c "
import pkg_resources
required = open('requirements.txt').read().splitlines()
installed = [pkg.key for pkg in pkg_resources.working_set]
missing = [pkg for pkg in required if pkg.split('==')[0].lower() not in installed]
if missing:
    print(f'Missing packages: {missing}')
else:
    print('All required packages are installed')
"
```

### 10.3 Test Individual Components
```bash
python -c "import mysql.connector; print('MySQL connector OK')"
python -c "import flask; print('Flask OK')"
python -c "from app.models import customer; print('Models OK')"
```

### 10.4 Check File Encoding
```bash
file -i *.py
```

---

## Step 11: Web App Configuration Commands

### 11.1 Check Current Directory Path
```bash
pwd
```

### 11.2 Get Absolute Path for Web App Configuration
```bash
readlink -f .
```

### 11.3 Verify WSGI File Path
```bash
readlink -f wsgi.py
```

---

## Common Issues and Solutions

### Issue 1: Module Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 2: Database Connection Pool Issues
```bash
# Test with minimal connection pool
python -c "
import mysql.connector
conn = mysql.connector.connect(
    host='your_host',
    user='your_user', 
    password='your_password',
    database='your_database',
    pool_size=1,
    pool_reset_session=False
)
print('Minimal connection successful')
conn.close()
"
```

### Issue 3: Template Not Found Errors
```bash
# Check template directories
find . -name "templates" -type d
find . -name "*.html" | grep -E "(base|layout|index)"
```

### Issue 4: Static Files Not Loading
```bash
# Check static file structure
find . -name "static" -type d
find . -path "*/static/*" -name "*.css"
find . -path "*/static/*" -name "*.js"
```

---

## Final Verification Commands

### Before Going Live
```bash
# 1. Verify all dependencies
pip check

# 2. Test database connection
python -c "from wsgi import application; print('Ready for deployment')"

# 3. Check file permissions
ls -la wsgi.py

# 4. Verify project structure
tree -L 3  # if tree is available, otherwise use ls -la
```

---

## Notes

1. Replace `your_username`, `your_password`, and `your_host` with your actual PythonAnywhere credentials
2. The database name format on PythonAnywhere is `username$database_name`
3. All commands should be run in the project root directory unless specified otherwise
4. Keep the virtual environment activated throughout the deployment process
5. Some commands may take several minutes to complete, especially dependency installation

## Web App Configuration

After running all bash commands successfully:

1. Go to PythonAnywhere Web tab
2. Click "Add a new web app"
3. Choose Manual configuration with Python 3.10
4. Set source code directory to: `/home/yourusername/automotive-repair-management-system`
5. Set WSGI configuration file to: `/home/yourusername/automotive-repair-management-system/wsgi.py`
6. Set virtualenv to: `/home/yourusername/automotive-repair-management-system/venv`
7. Click "Reload" to deploy the application

Your application should now be accessible at `https://yourusername.pythonanywhere.com` 