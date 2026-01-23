<div align="center">

[![Project Banner](./public/selwyn-panel-beaters-online.svg)](#)

# Selwyn Panel Beaters Online Service
### Automotive Repair Management System

A modern automotive repair shop management solution built with Flask, SQLAlchemy, and PostgreSQL.

Deployed on **Heroku** with **Neon PostgreSQL** database and **Google OAuth** authentication.

[Features](#-key-features) | [Installation](#-getting-started) | [Deployment](#-deployment) | [API](#-api-endpoints) | [Issues][github-issues-link]

---

[![][python-shield]][python-link]
[![][flask-shield]][flask-link]
[![][postgresql-shield]][postgresql-link]
[![][heroku-shield]][heroku-link]
[![][license-shield]][license-link]

**[Live Demo](https://automotive-repair-system-d51413a4c459.herokuapp.com)**

</div>

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Backend Language |
| Flask | 3.0.1 | Web Framework |
| SQLAlchemy | 2.0.25 | ORM |
| PostgreSQL | 14+ | Database (Neon Cloud) |
| Authlib | 1.3.0 | Google OAuth Integration |
| Gunicorn | 21.2.0 | Production WSGI Server |
| Bootstrap | 5.3 | Frontend UI Framework |

---

## Key Features

### For Technicians
- **Job Management** - View and manage repair orders
- **Service Tracking** - Add services and parts to jobs
- **Real-time Costing** - Automatic cost calculation
- **Job Completion** - Mark jobs as completed with notes

### For Administrators
- **Customer Management** - Full CRUD for customer records
- **Billing System** - Process payments and track invoices
- **Overdue Tracking** - Monitor overdue payments
- **Reports** - Business analytics and reporting

### Authentication
- **Google OAuth 2.0** - One-click sign-in with Google
- **Traditional Login** - Username/password authentication
- **Role-based Access** - Technician and Administrator roles
- **Secure Sessions** - Flask session management with CSRF protection

---

## Project Structure

```
automotive-repair-management-system/
├── app/
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── customer.py      # Customer model
│   │   ├── job.py           # Job and related models
│   │   ├── service.py       # Service model
│   │   ├── part.py          # Part model
│   │   └── user.py          # User authentication model
│   ├── services/            # Business logic layer
│   │   ├── auth_service.py  # Authentication service
│   │   ├── oauth_service.py # Google OAuth integration
│   │   ├── job_service.py   # Job operations
│   │   └── billing_service.py
│   ├── views/               # Flask blueprints (routes)
│   │   ├── main.py          # Main routes
│   │   ├── auth.py          # OAuth routes
│   │   ├── technician.py    # Technician portal
│   │   └── administrator.py # Admin portal
│   ├── templates/           # Jinja2 HTML templates
│   ├── static/              # CSS, JavaScript assets
│   ├── utils/               # Utilities and helpers
│   └── extensions.py        # Flask extensions (SQLAlchemy)
├── config/                  # Configuration classes
├── scripts/
│   ├── database/            # SQL schema files
│   └── setup_neon.py        # Neon database setup
├── docs/deployment/         # Deployment guides
├── tests/                   # Test suite
├── Procfile                 # Heroku process file
├── requirements.txt         # Python dependencies
├── run.py                   # Development server
└── wsgi.py                  # Production WSGI entry
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for Neon CLI)
- Git
- Google Cloud Console account (for OAuth)

### Quick Installation

**1. Clone Repository**

```bash
git clone https://github.com/ChanMeng666/automotive-repair-management-system.git
cd automotive-repair-management-system
```

**2. Create Virtual Environment**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Set Up Neon Database**

```bash
# Option A: Use the setup script
python scripts/setup_neon.py

# Option B: Manual setup with Neon CLI
npm install -g neonctl
neonctl auth
neonctl projects create --name automotive-repair
neonctl connection-string PROJECT_ID
```

**5. Configure Environment**

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL and OAuth credentials
```

**6. Set Up Google OAuth** (Optional for local dev)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create OAuth 2.0 Client ID
3. Add redirect URI: `http://localhost:5000/auth/google/callback`
4. Copy Client ID and Secret to `.env`

**7. Initialize Database**

```bash
# Using psql
psql "YOUR_DATABASE_URL" -f scripts/database/schema.sql

# Or use Neon SQL Editor in the dashboard
```

**8. Run Application**

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## Deployment

### Deploy to Heroku

**1. Prerequisites**

```bash
# Install Heroku CLI
npm install -g heroku

# Login
heroku login
```

**2. Create Heroku App**

```bash
heroku create your-app-name
```

**3. Configure Environment Variables**

```bash
# Database (Neon PostgreSQL)
heroku config:set DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require"

# Flask Configuration
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set FLASK_ENV=production
heroku config:set LOG_TO_STDOUT=true

# Google OAuth
heroku config:set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
heroku config:set GOOGLE_CLIENT_SECRET="your-client-secret"
```

**4. Deploy**

```bash
git push heroku main
```

**5. Open Application**

```bash
heroku open
```

### Google OAuth Setup for Production

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Add Authorized redirect URI:
   ```
   https://your-app-name.herokuapp.com/auth/google/callback
   ```
4. Add Authorized JavaScript origin:
   ```
   https://your-app-name.herokuapp.com
   ```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Neon PostgreSQL connection string |
| `SECRET_KEY` | Yes | Flask session encryption key |
| `FLASK_ENV` | No | `development` or `production` |
| `GOOGLE_CLIENT_ID` | No* | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | No* | Google OAuth Client Secret |
| `LOG_TO_STDOUT` | No | Set `true` for cloud logging |

*Required for Google Sign-In functionality

---

## API Endpoints

### Public Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page / Dashboard |
| GET | `/login` | Login page |
| POST | `/login` | Process login |
| GET | `/logout` | Logout user |

### OAuth Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google` | Initiate Google OAuth |
| GET | `/auth/google/callback` | Google OAuth callback |
| GET | `/auth/session` | Get current session info |

### Technician Routes (requires auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/technician/current_jobs` | List current jobs |
| GET | `/technician/new_job` | Create new job form |
| POST | `/technician/new_job` | Create new job |
| GET/POST | `/technician/job/<id>` | View/edit job |
| POST | `/technician/job/<id>/add_service` | Add service to job |
| POST | `/technician/job/<id>/add_part` | Add part to job |
| POST | `/technician/job/<id>/complete` | Mark job complete |

### Administrator Routes (requires admin role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/administrator/dashboard` | Admin dashboard |
| GET | `/administrator/customers` | Customer list |
| GET/POST | `/administrator/customer/<id>` | Customer details |
| GET | `/administrator/billing` | Billing management |
| GET | `/administrator/overdue` | Overdue bills |
| GET | `/administrator/reports` | Reports |

---

## Database Schema

### Core Tables

- **customer** - Customer information
- **job** - Repair job records
- **service** - Available services
- **part** - Parts inventory
- **job_service** - Services on jobs (junction)
- **job_part** - Parts on jobs (junction)
- **user** - User authentication

### Relationships

```
Customer (1) ──────< (Many) Job
Job (Many) >────────< (Many) Service  [via job_service]
Job (Many) >────────< (Many) Part     [via job_part]
```

---

## Development

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/unit/test_models.py -v
```

### Code Quality

```bash
# Linting
flake8 app/

# Security scan
bandit -r app/
```

### Database Migrations

Using Alembic (included in SQLAlchemy):

```bash
# Create migration
flask db migrate -m "Add new field"

# Apply migration
flask db upgrade

# Rollback
flask db downgrade
```

---

## Documentation

- [Heroku Deployment Guide](docs/deployment/heroku.md)
- [Neon Database Setup](docs/deployment/neon.md)
- [Quick Start Guide](docs/deployment/quick_start.md)

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Author

**Chan Meng**

- Website: [chanmeng.live](https://chanmeng.live)
- GitHub: [@ChanMeng666](https://github.com/ChanMeng666)
- LinkedIn: [chanmeng666](https://www.linkedin.com/in/chanmeng666/)

---

<div align="center">

**Built with Flask, SQLAlchemy, Neon PostgreSQL, and Google OAuth**

[Report Bug][github-issues-link] · [Request Feature][github-issues-link]

</div>

<!-- Links -->
[github-issues-link]: https://github.com/ChanMeng666/automotive-repair-management-system/issues
[python-link]: https://python.org
[flask-link]: https://flask.palletsprojects.com
[postgresql-link]: https://neon.tech
[heroku-link]: https://heroku.com

[python-shield]: https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white
[flask-shield]: https://img.shields.io/badge/Flask-3.0.1-000000?style=for-the-badge&logo=flask&logoColor=white
[postgresql-shield]: https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white
[heroku-shield]: https://img.shields.io/badge/Heroku-Deployed-430098?style=for-the-badge&logo=heroku&logoColor=white
[license-shield]: https://img.shields.io/badge/License-MIT-green?style=for-the-badge
