# Quick Start Guide

Get the Automotive Repair Management System running in 5 minutes.

## Prerequisites

- Python 3.10+
- Git
- Neon account ([sign up](https://neon.tech))
- Heroku account ([sign up](https://signup.heroku.com)) - for deployment

---

## Local Development (5 minutes)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/ChanMeng666/automotive-repair-management-system.git
cd automotive-repair-management-system

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Run the Neon setup script
python scripts/setup_neon.py
```

Or manually create a Neon database and add to `.env`:

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL
```

### 3. Initialize Schema

```bash
psql "YOUR_DATABASE_URL" -f scripts/database/schema.sql
```

### 4. Run Application

```bash
python run.py
```

Open http://localhost:5000

---

## Production Deployment (10 minutes)

### 1. Install Heroku CLI

```bash
npm install -g heroku
heroku login
```

### 2. Create Heroku App

```bash
heroku create your-app-name
```

### 3. Configure Environment

```bash
# Database
heroku config:set DATABASE_URL="your-neon-connection-string"

# Flask
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set FLASK_ENV=production
heroku config:set LOG_TO_STDOUT=true
```

### 4. Deploy

```bash
git push heroku main
heroku open
```

---

## Add Google OAuth (Optional)

### 1. Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID
3. Set redirect URI: `https://repairos.chanmeng.org/auth/google/callback`

### 2. Configure Heroku

```bash
heroku config:set GOOGLE_CLIENT_ID="your-client-id"
heroku config:set GOOGLE_CLIENT_SECRET="your-secret"
```

---

## Default Login

If Google OAuth is not configured, use traditional login:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | (set in database) |
| Technician | tech | (set in database) |

---

## Useful Commands

```bash
# View logs
heroku logs --tail

# Check config
heroku config

# Open app
heroku open

# Run shell
heroku run bash
```

---

## Next Steps

- [Full Heroku Guide](heroku.md)
- [Neon Database Setup](neon.md)
- [API Documentation](../../README.md#-api-endpoints)

---

## Troubleshooting

**App crashes on startup:**
```bash
heroku logs --tail
# Check for missing environment variables
heroku config
```

**Database connection fails:**
- Verify DATABASE_URL is set correctly
- Ensure `?sslmode=require` is in the URL

**Google OAuth not working:**
- Check redirect URI matches exactly
- Verify Client ID and Secret are correct
- Make sure OAuth app is published (not in test mode)

---

## Support

- [GitHub Issues](https://github.com/ChanMeng666/automotive-repair-management-system/issues)
- [Documentation](../../README.md)
