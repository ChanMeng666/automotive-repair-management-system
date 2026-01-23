# Neon PostgreSQL Setup Guide

This guide explains how to set up Neon PostgreSQL with Stack Auth for the Automotive Repair Management System.

## Prerequisites

- Node.js 18+ (for Neon CLI)
- Python 3.9+ (for setup script)
- A Neon account ([sign up here](https://neon.tech))

## Quick Setup with Script

The easiest way to set up Neon is using the provided setup script:

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

## Manual Setup

### Step 1: Install Neon CLI

```bash
# Using npm
npm install -g neonctl

# Or using Homebrew (macOS)
brew install neonctl

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

## Stack Auth Integration

Stack Auth provides authentication that integrates seamlessly with Neon.

### Step 1: Create Stack Auth Project

1. Go to [Stack Auth Console](https://app.stack-auth.com)
2. Create a new project
3. Copy your Project ID

### Step 2: Configure Stack Auth

Add to your `.env`:

```bash
STACK_AUTH_PROJECT_ID=your-stack-auth-project-id
```

### Step 3: Get JWKS URL

Your JWKS URL is:
```
https://api.stack-auth.com/api/v1/projects/YOUR_PROJECT_ID/.well-known/jwks.json
```

### Step 4: Configure Neon RLS (Optional)

For Row-Level Security with Stack Auth:

1. Go to Neon Console > Settings > RLS
2. Add Stack Auth as authentication provider
3. Paste your JWKS URL
4. Configure RLS policies in your database

## Neon CLI Commands Reference

### Projects

```bash
# List projects
neonctl projects list

# Create project
neonctl projects create --name my-project

# Delete project
neonctl projects delete PROJECT_ID
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

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `STACK_AUTH_PROJECT_ID` | Optional | Stack Auth project ID for JWT auth |
| `DB_SSLMODE` | No | SSL mode (default: `require`) |

## Heroku Configuration

Set environment variables in Heroku:

```bash
# Set DATABASE_URL
heroku config:set DATABASE_URL="postgresql://..."

# Set Stack Auth (if using)
heroku config:set STACK_AUTH_PROJECT_ID="your-project-id"

# Set Flask environment
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

## Connection Pooling

Neon provides built-in connection pooling. Use the pooled connection string for better performance:

1. In Neon Console, go to Connection Details
2. Enable "Pooled Connection"
3. Use the pooled connection string

The pooled URL contains `-pooler` in the hostname:
```
postgresql://user:pass@ep-xxx-pooler.neon.tech/db?sslmode=require
```

## Troubleshooting

### Connection Timeout

- Verify SSL mode is `require`
- Check if compute is suspended (auto-resumes on connection)
- Use pooled connection string

### Authentication Failed

- Reset password in Neon Console
- Verify username/password in connection string
- Check for special characters that need URL encoding

### Import Error

If schema import fails:
```bash
# Check for syntax errors
psql "CONNECTION_STRING" -f schema.sql 2>&1 | head -50
```

## Costs

| Feature | Free Tier | Pro ($19/mo) |
|---------|-----------|--------------|
| Compute Hours | 100/month | 300/month |
| Storage | 0.5 GB | 10 GB |
| Projects | 1 | 10 |
| Branches | Unlimited | Unlimited |

The free tier is sufficient for development and small production workloads.
