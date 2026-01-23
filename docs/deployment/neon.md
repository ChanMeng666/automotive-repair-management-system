# Neon PostgreSQL Setup Guide

This guide explains how to set up Neon PostgreSQL for the Automotive Repair Management System.

## What is Neon?

Neon is a serverless PostgreSQL database with:
- **Free tier** with 100 compute hours/month
- **Automatic scaling** and sleeping
- **Branching** for development/testing
- **Built-in connection pooling**

## Prerequisites

- Node.js 18+ (for Neon CLI)
- Python 3.9+ (for setup script)
- A Neon account ([sign up here](https://neon.tech))

---

## Quick Setup with Script

The easiest way to set up Neon:

```bash
python scripts/setup_neon.py
```

This script will:
1. Install Neon CLI if needed
2. Authenticate with your Neon account
3. Create a new project or use existing
4. Get the connection string
5. Initialize the database schema
6. Save configuration to `.env`

---

## Manual Setup

### Step 1: Install Neon CLI

```bash
# Using npm
npm install -g neonctl

# Verify installation
neonctl --version
```

### Step 2: Authenticate

```bash
neonctl auth
```

This opens a browser for authentication.

### Step 3: Create Project

```bash
# Create a new project
neonctl projects create --name automotive-repair

# List your projects
neonctl projects list
```

### Step 4: Get Connection String

```bash
# Get connection string (replace PROJECT_ID)
neonctl connection-string PROJECT_ID
```

The connection string looks like:
```
postgresql://user:password@ep-xxx-xxx-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### Step 5: Initialize Database

```bash
# Connect and run schema
psql "YOUR_CONNECTION_STRING" -f scripts/database/schema.sql
```

Or use the Neon SQL Editor in the dashboard.

### Step 6: Configure Application

Add to your `.env` file:

```bash
DATABASE_URL=postgresql://user:password@ep-xxx.neon.tech/neondb?sslmode=require
```

---

## Neon CLI Commands

### Projects

```bash
# List projects
neonctl projects list

# Create project
neonctl projects create --name my-project

# Delete project
neonctl projects delete PROJECT_ID

# Get project details
neonctl projects get PROJECT_ID
```

### Branches

```bash
# List branches
neonctl branches list --project-id PROJECT_ID

# Create branch (for dev/testing)
neonctl branches create --project-id PROJECT_ID --name dev

# Get connection string for branch
neonctl connection-string PROJECT_ID --branch dev
```

### Databases

```bash
# List databases
neonctl databases list --project-id PROJECT_ID

# Create database
neonctl databases create --project-id PROJECT_ID --name mydb
```

### Account

```bash
# View current account
neonctl me

# Logout
neonctl auth logout
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `DB_SSLMODE` | No | SSL mode (default: `require`) |

---

## Heroku Configuration

Set environment variables in Heroku:

```bash
# Set DATABASE_URL
heroku config:set DATABASE_URL="postgresql://..."

# Set Flask environment
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set LOG_TO_STDOUT=true

# Set Google OAuth (optional)
heroku config:set GOOGLE_CLIENT_ID="your-client-id"
heroku config:set GOOGLE_CLIENT_SECRET="your-secret"
```

---

## Connection Pooling

Neon provides built-in connection pooling for better performance.

### Enable Pooling

1. In Neon Console, go to **Connection Details**
2. Enable **"Pooled Connection"**
3. Use the pooled connection string

### Pooled URL Format

The pooled URL contains `-pooler` in the hostname:
```
postgresql://user:pass@ep-xxx-pooler.neon.tech/db?sslmode=require
```

### When to Use Pooling

- High-concurrency applications
- Serverless deployments
- Connection limit issues

---

## Database Schema

The schema file is located at `scripts/database/schema.sql`.

### Initialize Schema

```bash
# Using psql
psql "YOUR_CONNECTION_STRING" -f scripts/database/schema.sql

# Using Neon SQL Editor
# 1. Go to Neon Console
# 2. Select your project
# 3. Open SQL Editor
# 4. Paste and run the schema
```

### Tables

| Table | Description |
|-------|-------------|
| `customer` | Customer information |
| `job` | Repair job records |
| `service` | Available services |
| `part` | Parts inventory |
| `job_service` | Services on jobs (junction) |
| `job_part` | Parts on jobs (junction) |
| `user` | User authentication |

---

## Branching for Development

Neon supports database branching for isolated development:

### Create Development Branch

```bash
# Create branch from main
neonctl branches create --project-id PROJECT_ID --name dev

# Get connection string for branch
neonctl connection-string PROJECT_ID --branch dev
```

### Use Cases

- **Feature development** - Test changes without affecting production
- **CI/CD** - Create branches for each pull request
- **Data testing** - Experiment with production-like data

### Delete Branch

```bash
neonctl branches delete --project-id PROJECT_ID dev
```

---

## Troubleshooting

### Connection Timeout

**Cause:** Compute is suspended (auto-sleep after inactivity)

**Solution:** First request wakes the compute (5-10 second delay)

### Authentication Failed

**Solutions:**
1. Reset password in Neon Console
2. Verify username/password in connection string
3. URL-encode special characters in password

### SSL Connection Error

**Solution:** Ensure `sslmode=require` in connection string

### Import Error

```bash
# Check for syntax errors
psql "CONNECTION_STRING" -f schema.sql 2>&1 | head -50
```

---

## Neon vs Other Options

| Feature | Neon | Heroku Postgres | Supabase |
|---------|------|-----------------|----------|
| Free Tier | 100 compute hours | 10K rows | 500MB |
| Serverless | Yes | No | Yes |
| Branching | Yes | No | No |
| Auto-sleep | Yes | No | Yes |
| Connection Pool | Built-in | Add-on | Built-in |

---

## Costs

| Plan | Cost | Features |
|------|------|----------|
| Free | $0 | 100 compute hours, 0.5GB |
| Launch | $19/mo | 300 compute hours, 10GB |
| Scale | $69/mo | 750 compute hours, 50GB |

The free tier is sufficient for development and small production workloads.

---

## Security Best Practices

1. **Use SSL**: Always use `sslmode=require`
2. **Rotate credentials**: Change passwords periodically
3. **IP restrictions**: Configure allowed IPs in Neon Console
4. **Audit logs**: Monitor connection attempts
5. **Backup**: Enable point-in-time recovery (Pro plan)

---

## Resources

- [Neon Documentation](https://neon.tech/docs)
- [Neon CLI Reference](https://neon.tech/docs/reference/cli)
- [PostgreSQL Tutorial](https://neon.tech/postgresql)
- [Neon Discord Community](https://discord.gg/92vNTzKDGp)
