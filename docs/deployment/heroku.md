# Heroku Deployment Guide

Complete guide to deploying the Automotive Repair Management System to Heroku with Neon PostgreSQL.

## Prerequisites

- Heroku account ([sign up](https://signup.heroku.com))
- Heroku CLI ([download](https://devcenter.heroku.com/articles/heroku-cli))
- Git installed
- Neon database set up (see [neon.md](neon.md))

## Quick Deploy

### Step 1: Login to Heroku

```bash
heroku login
```

### Step 2: Create App

```bash
heroku create your-app-name

# Or let Heroku generate a name
heroku create
```

### Step 3: Configure Database

**Option A: Use Neon PostgreSQL (Recommended)**

```bash
heroku config:set DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require"
```

**Option B: Use Heroku Postgres**

```bash
heroku addons:create heroku-postgresql:mini
```

### Step 4: Set Environment Variables

```bash
# Generate and set secret key
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Set Flask environment
heroku config:set FLASK_ENV=production

# Enable stdout logging
heroku config:set LOG_TO_STDOUT=true

# Optional: Stack Auth
heroku config:set STACK_AUTH_PROJECT_ID="your-stack-auth-project-id"
```

### Step 5: Deploy

```bash
git push heroku main
```

### Step 6: Initialize Database

```bash
# If using Neon (schema already applied via setup script)
# Or run manually:
heroku run "psql \$DATABASE_URL -f scripts/database/schema.sql"
```

### Step 7: Open Application

```bash
heroku open
```

## Configuration Files

### Procfile

The project includes a `Procfile` for Heroku:

```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### runtime.txt

Specifies Python version:

```
python-3.10.13
```

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | PostgreSQL URL | `postgresql://...` |
| `SECRET_KEY` | Yes | Flask secret | 64-char hex |
| `FLASK_ENV` | Yes | Environment | `production` |
| `LOG_TO_STDOUT` | Yes | Cloud logging | `true` |
| `STACK_AUTH_PROJECT_ID` | No | Stack Auth | `abc123` |

## Using Neon with Heroku

### Why Neon?

- Free tier with 100 compute hours/month
- Serverless scaling
- Built-in connection pooling
- Stack Auth integration

### Setup Steps

1. **Create Neon Project**

```bash
# Using Neon CLI
neonctl auth
neonctl projects create --name automotive-repair
neonctl connection-string PROJECT_ID
```

2. **Set in Heroku**

```bash
heroku config:set DATABASE_URL="postgresql://..."
```

3. **Initialize Schema**

The schema is in `scripts/database/schema.sql`. Initialize it:

```bash
psql "YOUR_NEON_URL" -f scripts/database/schema.sql
```

## Stack Auth Integration

Stack Auth provides JWT-based authentication that works with Neon.

### Setup

1. Create account at [Stack Auth](https://app.stack-auth.com)
2. Create a new project
3. Get your Project ID
4. Configure in Heroku:

```bash
heroku config:set STACK_AUTH_PROJECT_ID="your-project-id"
```

### How It Works

1. Users authenticate via Stack Auth
2. Stack Auth issues JWT tokens
3. App validates tokens via JWKS
4. Users are created/linked automatically

## Useful Commands

### Logs

```bash
# View logs
heroku logs --tail

# Filter by dyno
heroku logs --dyno web
```

### Shell Access

```bash
# Run one-off command
heroku run python -c "from app import create_app; print('OK')"

# Interactive shell
heroku run bash
```

### Database

```bash
# Connect to database
heroku run psql \$DATABASE_URL

# For Neon, use your Neon connection string directly
```

### Scaling

```bash
# Scale to 1 web dyno
heroku ps:scale web=1

# Check status
heroku ps
```

## Troubleshooting

### Application Error (H10)

1. Check logs: `heroku logs --tail`
2. Verify all env vars are set: `heroku config`
3. Ensure database is initialized

### Database Connection Error

1. Verify DATABASE_URL: `heroku config:get DATABASE_URL`
2. Ensure SSL mode is `require`
3. For Neon: compute may be suspended, first request wakes it

### Memory Issues (R14)

1. Reduce gunicorn workers in Procfile
2. Upgrade dyno type
3. Optimize database queries

### Static Files Not Loading

Flask serves static files in development. For production:
- Files are served via Flask
- Consider using a CDN for high-traffic apps

## Continuous Deployment

### GitHub Integration

1. Go to Heroku Dashboard > Deploy
2. Connect to GitHub
3. Enable "Automatic Deploys"
4. Optionally: "Wait for CI to pass"

### Manual Deploy

```bash
git push heroku main
```

## Costs

### Heroku

| Plan | Cost | Features |
|------|------|----------|
| Eco | $5/mo | 1000 dyno hours |
| Basic | $7/mo | Always-on |

### Neon (Database)

| Plan | Cost | Features |
|------|------|----------|
| Free | $0 | 100 compute hours |
| Pro | $19/mo | 300 compute hours |

**Total minimum cost: $5-7/month** (Heroku only, Neon free tier)

## Security Checklist

- [ ] SECRET_KEY is set and secure
- [ ] FLASK_ENV is `production`
- [ ] DATABASE_URL uses SSL (`sslmode=require`)
- [ ] No sensitive data in git history
- [ ] Stack Auth configured (if using JWT)

## Custom Domain

```bash
# Add domain
heroku domains:add www.yourdomain.com

# Get DNS target
heroku domains

# Configure DNS with CNAME to target

# Enable SSL
heroku certs:auto:enable
```
