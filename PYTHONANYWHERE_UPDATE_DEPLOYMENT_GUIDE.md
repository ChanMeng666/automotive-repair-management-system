# PythonAnywhere Update and Redeployment Guide

## Complete Guide for Updating Your Deployed Automotive Repair Management System

This guide covers how to update and redeploy your automotive repair management system on PythonAnywhere after the initial successful deployment. It includes various scenarios such as style changes, code updates, database modifications, and dependency updates.

## Prerequisites

- Project already successfully deployed on PythonAnywhere
- Access to PythonAnywhere bash console
- GitHub repository with the latest changes
- Basic familiarity with git commands

---

## Quick Reference: Common Update Scenarios

| Update Type | Time Required | Reload Required | Database Impact |
|-------------|---------------|-----------------|-----------------|
| CSS/JS Changes | 2-5 minutes | Yes | None |
| HTML Template Changes | 2-5 minutes | Yes | None |
| Python Code Changes | 5-10 minutes | Yes | None |
| New Dependencies | 10-15 minutes | Yes | None |
| Database Schema Changes | 15-30 minutes | Yes | High |
| Configuration Changes | 5-10 minutes | Yes | Medium |

---

## Step 1: Accessing Your Deployed Project

### 1.1 Login to PythonAnywhere Bash Console
```bash
# Navigate to your project directory
cd ~/automotive-repair-management-system

# Check current status
pwd
ls -la
```

### 1.2 Activate Virtual Environment
```bash
# Always activate virtual environment before making changes
source venv/bin/activate

# Verify activation
which python
which pip
```

### 1.3 Check Current Deployment Status
```bash
# Check current git status
git status
git log --oneline -5

# Check if web app is running
curl -I https://yourusername.pythonanywhere.com
```

---

## Step 2: Updating Code from GitHub

### 2.1 Fetch Latest Changes
```bash
# Fetch all remote changes
git fetch origin

# Check what changes are available
git log HEAD..origin/main --oneline
```

### 2.2 Pull Updates
```bash
# Pull latest changes from main branch
git pull origin main

# If there are conflicts, resolve them
git status
```

### 2.3 Handle Merge Conflicts (if any)
```bash
# View conflicted files
git diff --name-only --diff-filter=U

# Edit conflicted files manually, then:
git add .
git commit -m "Resolve merge conflicts"
```

---

## Step 3: Style and Template Updates

### 3.1 CSS Changes
```bash
# Check CSS files
ls -la app/static/css/
cat app/static/css/main.css

# If you made CSS changes, verify file integrity
file app/static/css/main.css
```

### 3.2 JavaScript Changes
```bash
# Check JS files
ls -la app/static/js/
cat app/static/js/main.js

# Test JS syntax (if node is available)
node -c app/static/js/main.js 2>/dev/null && echo "JS syntax OK" || echo "JS syntax error"
```

### 3.3 HTML Template Changes
```bash
# Check template files
find . -name "*.html" -type f -newer /tmp/last_deploy 2>/dev/null || find . -name "*.html" -type f

# Verify template syntax (basic check)
python -c "
import os
from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

template_dirs = ['app/templates', 'templates']
for template_dir in template_dirs:
    if os.path.exists(template_dir):
        env = Environment(loader=FileSystemLoader(template_dir))
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.html'):
                    try:
                        template_path = os.path.relpath(os.path.join(root, file), template_dir)
                        env.get_template(template_path)
                        print(f'✓ {template_path}')
                    except TemplateSyntaxError as e:
                        print(f'✗ {template_path}: {e}')
"
```

### 3.4 Static File Permissions
```bash
# Ensure proper permissions for static files
chmod -R 644 app/static/css/*.css
chmod -R 644 app/static/js/*.js
chmod -R 644 app/static/images/*

# Check permissions
ls -la app/static/css/
ls -la app/static/js/
```

---

## Step 4: Python Code Updates

### 4.1 Test Code Syntax
```bash
# Check Python syntax for all Python files
find . -name "*.py" -exec python -m py_compile {} \;

# If syntax errors exist, they will be reported
echo "Python syntax check completed"
```

### 4.2 Test Application Imports
```bash
# Test main application import
python -c "
try:
    from wsgi import application
    print('✓ WSGI application imports successfully')
except Exception as e:
    print(f'✗ WSGI import failed: {e}')
"

# Test Flask app import
python -c "
try:
    import app
    print('✓ Flask app imports successfully')
except Exception as e:
    print(f'✗ Flask app import failed: {e}')
"
```

### 4.3 Test Database Connectivity
```bash
# Test database connection with updated code
python -c "
import mysql.connector
try:
    from config.base import Config
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        pool_size=1
    )
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM customers')
    count = cursor.fetchone()[0]
    print(f'✓ Database connection OK. Records: {count}')
    conn.close()
except Exception as e:
    print(f'✗ Database connection failed: {e}')
"
```

---

## Step 5: Dependency Updates

### 5.1 Check for New Dependencies
```bash
# Compare current and new requirements
pip freeze > current_requirements.txt
diff requirements.txt current_requirements.txt || echo "Dependencies changed"
```

### 5.2 Install New Dependencies
```bash
# Install/update dependencies
pip install -r requirements.txt

# Verify installation
pip check

# List installed packages
pip list | grep -E "(flask|mysql|jinja2)"
```

### 5.3 Handle Dependency Conflicts
```bash
# If there are conflicts, resolve them
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall

# Clean up
rm current_requirements.txt
```

---

## Step 6: Configuration Updates

### 6.1 Update Configuration Files
```bash
# Check if configuration files changed
ls -la config/
cat config/base.py

# Run configuration update if needed
python update_db_config.py
```

### 6.2 Environment Variables
```bash
# Check current environment variables
printenv | grep -E "(FLASK|MYSQL|DATABASE)"

# Set new environment variables if needed
export FLASK_ENV=production
export FLASK_APP=wsgi.py
```

### 6.3 WSGI Configuration Check
```bash
# Verify WSGI file is correct
cat wsgi.py

# Test WSGI application
python -c "
try:
    from wsgi import application
    print('✓ WSGI configuration is valid')
except Exception as e:
    print(f'✗ WSGI configuration error: {e}')
"
```

---

## Step 7: Database Updates

### 7.1 Backup Current Database
```bash
# Create database backup before making changes
mysql -u yourusername -p -h yourusername.mysql.pythonanywhere-services.com yourusername\$spb -e "
SELECT COUNT(*) as customers FROM customers;
SELECT COUNT(*) as jobs FROM jobs;
SELECT COUNT(*) as parts FROM parts;
SELECT COUNT(*) as services FROM services;
" > database_backup_$(date +%Y%m%d_%H%M%S).txt

echo "Database backup created"
```

### 7.2 Apply Database Schema Changes (if any)
```bash
# If there are new SQL files or schema changes
ls -la *.sql

# Apply schema changes (be very careful!)
# mysql -u yourusername -p -h yourusername.mysql.pythonanywhere-services.com yourusername\$spb < new_schema_changes.sql
```

### 7.3 Verify Database Integrity
```bash
# Test database after changes
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
    cursor = conn.cursor()
    
    # Test each table
    tables = ['customers', 'jobs', 'parts', 'services']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f'✓ {table}: {count} records')
    
    conn.close()
    print('✓ Database integrity check passed')
except Exception as e:
    print(f'✗ Database integrity check failed: {e}')
"
```

---

## Step 8: Final Testing Before Reload

### 8.1 Comprehensive Application Test
```bash
# Test all major components
python -c "
import sys
import traceback

tests = [
    ('Flask Import', lambda: __import__('flask')),
    ('MySQL Connector', lambda: __import__('mysql.connector')),
    ('App Module', lambda: __import__('app')),
    ('WSGI Application', lambda: __import__('wsgi').application),
    ('Config Module', lambda: __import__('config.base').base.Config),
]

print('Running pre-deployment tests...')
failed_tests = []

for test_name, test_func in tests:
    try:
        test_func()
        print(f'✓ {test_name}')
    except Exception as e:
        print(f'✗ {test_name}: {e}')
        failed_tests.append(test_name)

if failed_tests:
    print(f'\\nFailed tests: {failed_tests}')
    print('Fix issues before reloading the web app!')
    sys.exit(1)
else:
    print('\\n✓ All tests passed. Ready for deployment!')
"
```

### 8.2 Check File Permissions
```bash
# Ensure all files have correct permissions
find . -name "*.py" -exec chmod 644 {} \;
chmod 755 .
chmod -R 644 app/static/
```

### 8.3 Clean Up Temporary Files
```bash
# Remove temporary files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
```

---

## Step 9: Reload the Web Application

### 9.1 Using PythonAnywhere Web Interface
```
1. Go to https://www.pythonanywhere.com/user/yourusername/webapps/
2. Click on your domain (yourusername.pythonanywhere.com)
3. Click the green "Reload" button
4. Wait for the reload to complete (usually 10-30 seconds)
```

### 9.2 Using API (Alternative Method)
```bash
# If you have API token configured
curl -X POST \
  -H "Authorization: Token YOUR_API_TOKEN" \
  https://www.pythonanywhere.com/api/v0/user/yourusername/webapps/yourusername.pythonanywhere.com/reload/
```

### 9.3 Verify Reload Success
```bash
# Check if the app is responding
curl -I https://yourusername.pythonanywhere.com

# Check response time
time curl -s https://yourusername.pythonanywhere.com > /dev/null
```

---

## Step 10: Post-Deployment Verification

### 10.1 Test Website Functionality
```bash
# Test main pages
curl -s https://yourusername.pythonanywhere.com | grep -q "automotive" && echo "✓ Homepage working" || echo "✗ Homepage failed"

curl -s https://yourusername.pythonanywhere.com/customers | grep -q "customer" && echo "✓ Customers page working" || echo "✗ Customers page failed"

curl -s https://yourusername.pythonanywhere.com/currentjoblist | grep -q "job" && echo "✓ Jobs page working" || echo "✗ Jobs page failed"
```

### 10.2 Test Database Operations
```bash
# Test database connectivity through web app
curl -s https://yourusername.pythonanywhere.com/test | grep -q "Database" && echo "✓ Database test working" || echo "✗ Database test failed"
```

### 10.3 Check Error Logs
```bash
# Check for any error logs (if logging is configured)
ls -la logs/ 2>/dev/null || echo "No logs directory"

# Check PythonAnywhere error logs through web interface
echo "Check error logs at: https://www.pythonanywhere.com/user/yourusername/webapps/"
```

---

## Step 11: Rollback Procedures (If Problems Occur)

### 11.1 Quick Rollback to Previous Version
```bash
# View recent commits
git log --oneline -10

# Rollback to previous commit (replace COMMIT_HASH with actual hash)
git reset --hard COMMIT_HASH

# Force push if necessary (be careful!)
# git push origin main --force
```

### 11.2 Restore Database Backup
```bash
# If database issues occur, restore from backup
# mysql -u yourusername -p -h yourusername.mysql.pythonanywhere-services.com yourusername\$spb < backup_file.sql
```

### 11.3 Emergency Revert
```bash
# In case of critical issues, revert to last known working state
git reflog
git reset --hard HEAD@{1}  # or appropriate reflog entry
```

---

## Common Update Scenarios and Commands

### Scenario 1: Only CSS/Style Changes
```bash
cd ~/automotive-repair-management-system
source venv/bin/activate
git pull origin main
# Reload web app through interface
```

### Scenario 2: Python Code Changes
```bash
cd ~/automotive-repair-management-system
source venv/bin/activate
git pull origin main
python -c "from wsgi import application; print('App OK')"
# Reload web app through interface
```

### Scenario 3: New Dependencies Added
```bash
cd ~/automotive-repair-management-system
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
pip check
python -c "from wsgi import application; print('App OK')"
# Reload web app through interface
```

### Scenario 4: Database Schema Changes
```bash
cd ~/automotive-repair-management-system
source venv/bin/activate
# Create backup first!
mysql -u yourusername -p -h yourusername.mysql.pythonanywhere-services.com yourusername\$spb -e "SELECT COUNT(*) FROM customers" > backup.txt
git pull origin main
# Apply schema changes carefully
# mysql -u yourusername -p -h yourusername.mysql.pythonanywhere-services.com yourusername\$spb < schema_changes.sql
python -c "from wsgi import application; print('App OK')"
# Reload web app through interface
```

---

## Best Practices for Updates

### 1. Always Test First
- Test changes in a development environment before deploying
- Use the pre-deployment test script provided above
- Make small, incremental changes rather than large updates

### 2. Backup Strategy
- Always backup database before schema changes
- Keep track of working commit hashes
- Document major changes in commit messages

### 3. Monitoring
- Check website functionality after each deployment
- Monitor error logs for issues
- Test database connectivity regularly

### 4. Update Schedule
- Plan updates during low-traffic periods
- Allow sufficient time for testing and rollback if needed
- Coordinate updates with any scheduled maintenance

---

## Troubleshooting Common Update Issues

### Issue 1: Import Errors After Update
```bash
# Check Python path and module conflicts
python -c "import sys; print('\\n'.join(sys.path))"
pip list | grep -E "(flask|mysql)"

# Reinstall dependencies if needed
pip install -r requirements.txt --force-reinstall
```

### Issue 2: Template Not Found Errors
```bash
# Check template file structure
find . -name "*.html" -type f
ls -la app/templates/
ls -la templates/

# Verify template paths in code
grep -r "render_template" app/ --include="*.py"
```

### Issue 3: Static Files Not Loading
```bash
# Check static file permissions and structure
ls -la app/static/
chmod -R 644 app/static/css/*.css
chmod -R 644 app/static/js/*.js
```

### Issue 4: Database Connection Issues
```bash
# Test database configuration
python -c "
from config.base import Config
print(f'Host: {Config.MYSQL_HOST}')
print(f'Database: {Config.MYSQL_DATABASE}')
print(f'User: {Config.MYSQL_USER}')
"

# Test connection with minimal pool
python -c "
import mysql.connector
conn = mysql.connector.connect(
    host='yourusername.mysql.pythonanywhere-services.com',
    user='yourusername',
    password='yourpassword',
    database='yourusername\$spb',
    pool_size=1
)
print('Database connection successful')
conn.close()
"
```

---

## Conclusion

Regular updates and redeployments are essential for maintaining your automotive repair management system. By following this guide, you can safely update your application while minimizing downtime and avoiding common pitfalls.

Remember to:
- Always test before deploying
- Create backups before major changes
- Follow the step-by-step process
- Monitor the application after updates
- Keep rollback procedures ready

For complex updates or major version changes, consider creating a staging environment to test thoroughly before applying changes to your production deployment. 