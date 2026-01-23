<div align="center">

[![Project Banner](./public/selwyn-panel-beaters-online.svg)](#)

# Selwyn Panel Beaters Online Service
### Automotive Repair Management System

A modern automotive repair shop management solution built with Flask and SQLAlchemy.

Deploy to **Heroku** with **Neon PostgreSQL** and **Stack Auth** authentication.

[Installation](#-getting-started) | [Deployment](#-deployment) | [Documentation](#-documentation) | [Issues][github-issues-link]

---

[![][python-shield]][python-link]
[![][flask-shield]][flask-link]
[![][postgresql-shield]][postgresql-link]
[![][license-shield]][license-link]

</div>

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.9+ | Backend Language |
| Flask | 3.0.1 | Web Framework |
| SQLAlchemy | 2.0 | ORM |
| PostgreSQL | 14+ | Database (Neon) |
| Stack Auth | - | JWT Authentication |
| Gunicorn | 21.2.0 | Production Server |

---

## Key Features

### Technician Workspace
- View and manage repair jobs
- Add services and parts
- Real-time cost calculation
- Mark jobs as completed

### Administrator Portal
- Customer management
- Job scheduling
- Billing and payments
- Inventory control

### Authentication
- Traditional username/password login
- Stack Auth JWT integration
- Role-based access control

---

## Project Structure

```
automotive-repair-management-system/
├── app/
│   ├── models/           # SQLAlchemy ORM models
│   ├── services/         # Business logic layer
│   ├── views/            # Flask blueprints
│   ├── templates/        # Jinja2 templates
│   ├── static/           # CSS, JS assets
│   ├── utils/            # Utilities
│   └── extensions.py     # Flask extensions (SQLAlchemy)
├── config/               # Configuration
├── scripts/
│   ├── database/         # SQL schemas
│   └── setup_neon.py     # Neon CLI setup
├── docs/deployment/      # Deployment guides
├── tests/                # Test suite
├── Procfile              # Heroku deployment
├── requirements.txt      # Dependencies
├── run.py                # Development server
└── wsgi.py               # Production WSGI
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+ (for Neon CLI)
- Git

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
# Run the setup script
python scripts/setup_neon.py
```

Or manually:

```bash
# Install Neon CLI
npm install -g neonctl

# Authenticate and create project
neonctl auth
neonctl projects create --name automotive-repair

# Get connection string
neonctl connection-string PROJECT_ID
```

**5. Configure Environment**

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL
```

**6. Initialize Database**

```bash
psql "YOUR_DATABASE_URL" -f scripts/database/schema.sql
```

**7. Run Application**

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000)

---

## Deployment

### Deploy to Heroku

**1. Create Heroku App**

```bash
heroku login
heroku create your-app-name
```

**2. Configure Database (Option A: Neon)**

```bash
# Set Neon DATABASE_URL
heroku config:set DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require"
```

**2. Configure Database (Option B: Heroku Postgres)**

```bash
heroku addons:create heroku-postgresql:mini
```

**3. Set Environment Variables**

```bash
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set FLASK_ENV=production
heroku config:set LOG_TO_STDOUT=true
```

**4. Deploy**

```bash
git push heroku main
```

**5. Initialize Database**

```bash
heroku run "psql \$DATABASE_URL -f scripts/database/schema.sql"
```

**6. Open App**

```bash
heroku open
```

### Stack Auth Setup (Optional)

1. Create account at [Stack Auth](https://app.stack-auth.com)
2. Create a new project
3. Configure in Heroku:

```bash
heroku config:set STACK_AUTH_PROJECT_ID="your-project-id"
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | Flask session encryption key |
| `FLASK_ENV` | No | `development` or `production` |
| `STACK_AUTH_PROJECT_ID` | No | Stack Auth project ID |
| `LOG_TO_STDOUT` | No | Set `true` for cloud logging |

---

## Documentation

- [Neon Setup Guide](docs/deployment/neon.md)
- [Heroku Deployment](docs/deployment/heroku.md)

---

## Development

### Run Tests

```bash
pytest
pytest --cov=app
```

### Database Migrations

Using Alembic (included):

```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "description"

# Apply migration
flask db upgrade
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard |
| GET/POST | `/currentjoblist` | Job list |
| GET/POST | `/job/<id>` | Job details |
| POST | `/add_service_to_job/<id>` | Add service |
| POST | `/add_part_to_job/<id>` | Add part |
| GET/POST | `/administrator_customer_list` | Customers |
| GET/POST | `/administrator_pay_bills` | Billing |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Author

**Chan Meng**
- GitHub: [@ChanMeng666](https://github.com/ChanMeng666)
- LinkedIn: [chanmeng666](https://www.linkedin.com/in/chanmeng666/)

---

<div align="center">

**Built with Flask, SQLAlchemy, Neon, and Stack Auth**

</div>

<!-- Links -->
[github-issues-link]: https://github.com/ChanMeng666/automotive-repair-management-system/issues
[python-link]: https://python.org
[flask-link]: https://flask.palletsprojects.com
[postgresql-link]: https://postgresql.org

[python-shield]: https://img.shields.io/badge/python-3.9+-blue?style=flat-square&logo=python&logoColor=white
[flask-shield]: https://img.shields.io/badge/Flask-3.0.1-black?style=flat-square&logo=flask&logoColor=white
[postgresql-shield]: https://img.shields.io/badge/PostgreSQL-Neon-blue?style=flat-square&logo=postgresql&logoColor=white
[license-shield]: https://img.shields.io/badge/license-MIT-brightgreen?style=flat-square
