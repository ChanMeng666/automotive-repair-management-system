# Heroku Deployment Guide

Complete guide to deploying the Automotive Repair Management System to Heroku with Neon PostgreSQL and Google OAuth.

## Prerequisites

- Heroku account ([sign up](https://signup.heroku.com))
- Heroku CLI ([download](https://devcenter.heroku.com/articles/heroku-cli))
- Git installed
- Neon database set up (see [neon.md](neon.md))
- Google Cloud Console account (for OAuth)

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

**Using Neon PostgreSQL (Recommended)**

```bash
heroku config:set DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require"
```

### Step 4: Set Environment Variables

```bash
# Generate and set secret key
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Set Flask environment
heroku config:set FLASK_ENV=production

# Enable stdout logging
heroku config:set LOG_TO_STDOUT=true
```

### Step 5: Configure Google OAuth

```bash
heroku config:set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
heroku config:set GOOGLE_CLIENT_SECRET="your-client-secret"
```

### Step 6: Deploy

```bash
git push heroku main
```

### Step 7: Initialize Database

```bash
# Run schema if not already done
heroku run "psql \$DATABASE_URL -f scripts/database/schema.sql"
```

### Step 8: Open Application

```bash
heroku open
```

---

## Google OAuth Setup

Google OAuth provides secure "Sign in with Google" functionality.

### Step 1: Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Click **"Create Credentials"** > **"OAuth client ID"**
4. Select **"Web application"**

### Step 2: Configure OAuth Client

**Application type:** Web application

**Authorized JavaScript origins:**
```
https://your-app-name.herokuapp.com
```

**Authorized redirect URIs:**
```
https://your-app-name.herokuapp.com/auth/google/callback
```

### Step 3: Set Credentials in Heroku

```bash
heroku config:set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
heroku config:set GOOGLE_CLIENT_SECRET="your-client-secret"
```

### Step 4: Publish OAuth App (Optional)

For public access:
1. Go to **OAuth consent screen**
2. Click **"Publish App"**
3. Confirm publication

> **Note:** In testing mode, only added test users can sign in.

---

## Configuration Files

### Procfile

```
web: gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### runtime.txt

```
python-3.10.13
```

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | Yes | Neon PostgreSQL URL | `postgresql://...` |
| `SECRET_KEY` | Yes | Flask secret key | 64-char hex string |
| `FLASK_ENV` | Yes | Environment | `production` |
| `LOG_TO_STDOUT` | Yes | Cloud logging | `true` |
| `GOOGLE_CLIENT_ID` | No* | Google OAuth ID | `xxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | No* | Google OAuth Secret | `GOCSPX-xxx` |

*Required for Google Sign-In functionality

---

## Useful Commands

### Logs

```bash
# View live logs
heroku logs --tail

# Filter by dyno
heroku logs --dyno web

# Recent logs
heroku logs -n 200
```

### Configuration

```bash
# View all config vars
heroku config

# Get specific variable
heroku config:get DATABASE_URL

# Set variable
heroku config:set KEY=value

# Remove variable
heroku config:unset KEY
```

### Shell Access

```bash
# Run one-off command
heroku run python -c "from app import create_app; print('OK')"

# Interactive shell
heroku run bash

# Python shell
heroku run python
```

### Database

```bash
# Connect to database
heroku run psql \$DATABASE_URL

# Run SQL file
heroku run "psql \$DATABASE_URL -f scripts/database/schema.sql"
```

### Scaling

```bash
# Check dyno status
heroku ps

# Scale web dynos
heroku ps:scale web=1

# Restart all dynos
heroku restart
```

---

## Troubleshooting

### Application Error (H10)

**Cause:** Application crash at startup

**Solutions:**
1. Check logs: `heroku logs --tail`
2. Verify all env vars: `heroku config`
3. Test locally: `python run.py`
4. Ensure `Procfile` exists and is correct

### Database Connection Error

**Cause:** Invalid or missing DATABASE_URL

**Solutions:**
1. Verify URL: `heroku config:get DATABASE_URL`
2. Ensure SSL mode: `?sslmode=require`
3. Neon compute may be sleeping (auto-wakes on request)
4. Check connection string format

### Google OAuth Error

**Cause:** Misconfigured OAuth credentials

**Solutions:**
1. Verify Client ID and Secret are set
2. Check redirect URI matches exactly:
   ```
   https://your-app.herokuapp.com/auth/google/callback
   ```
3. Ensure domain is in authorized origins
4. Publish OAuth app for public access

### Memory Issues (R14)

**Cause:** Memory quota exceeded

**Solutions:**
1. Reduce gunicorn workers in `Procfile`
2. Optimize database queries
3. Upgrade dyno type

### Static Files Not Loading

**Cause:** Flask static file serving

**Solutions:**
- Flask serves static files automatically
- For high-traffic: consider WhiteNoise or CDN

---

## Continuous Deployment

### GitHub Integration

1. Go to Heroku Dashboard > Deploy tab
2. Connect to GitHub repository
3. Enable **"Automatic Deploys"**
4. Optionally: **"Wait for CI to pass"**

### Manual Deploy

```bash
git push heroku main
```

### Rollback

```bash
# List releases
heroku releases

# Rollback to previous
heroku rollback

# Rollback to specific version
heroku rollback v5
```

---

## Custom Domain

```bash
# Add domain
heroku domains:add www.yourdomain.com

# Get DNS target
heroku domains

# Configure DNS: CNAME record to the target

# Enable SSL (automatic with paid dynos)
heroku certs:auto:enable
```

---

## Costs

### Heroku Pricing

| Plan | Cost | Features |
|------|------|----------|
| Eco | $5/month | 1000 dyno hours, sleeps after 30min |
| Basic | $7/month | Always on, 1 dyno |
| Standard | $25/month | Horizontal scaling |

### Neon Database (Free Tier)

- 100 compute hours/month
- 0.5 GB storage
- 1 project
- Unlimited branches

**Total Minimum Cost: $5-7/month** (Heroku Eco/Basic + Neon Free)

---

## Security Checklist

- [ ] `SECRET_KEY` is set and unique
- [ ] `FLASK_ENV` is `production`
- [ ] `DATABASE_URL` uses SSL (`sslmode=require`)
- [ ] Google OAuth credentials are configured
- [ ] No sensitive data in git history
- [ ] HTTPS enabled (automatic on Heroku)

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│    Browser      │────>│   Heroku App    │
│                 │     │   (Flask +      │
│                 │<────│    Gunicorn)    │
└─────────────────┘     └────────┬────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        v                        v                        v
┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Google OAuth  │      │ Neon PostgreSQL │      │    Neon Auth    │
│ (Sign In)     │      │   (Database)    │      │  (JWKS/JWT)     │
└───────────────┘      └─────────────────┘      └─────────────────┘
```
