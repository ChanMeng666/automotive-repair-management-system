# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run development server (auto-creates tables in dev mode)
python run.py

# Run all tests (uses SQLite in-memory, no DB setup needed)
pytest

# Run tests with coverage (minimum threshold: 70%)
pytest --cov=app

# Run by marker
pytest -m unit
pytest -m integration
pytest -m security

# Run single test file / single test
pytest tests/unit/test_models.py -v
pytest tests/unit/test_auth.py::TestUserModel::test_create_user -v

# Code formatting (line-length: 100)
black --line-length 100 .
isort .

# Production server
gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

## Architecture

Flask app factory (`create_app` in `app/__init__.py`) with SQLAlchemy 2.0. Entry points: `run.py` (dev), `wsgi.py` (production via Gunicorn).

### Multi-Tenant Model

Shared-schema multi-tenancy with `tenant_id` discriminator on all business data tables. The key relationship chain:

```
User (1) --< TenantMembership (role, status) >-- (1) Tenant
Tenant (1) --< Customer, Job, Service, Part, Inventory
Tenant (1) --- (1) Subscription (Stripe billing)
Job (1) --< JobService >-- Service
Job (1) --< JobPart >-- Part
Inventory (1) --< InventoryTransaction
```

**RBAC lives on `TenantMembership`, not `User`.** Role constants (`ROLE_OWNER`, `ROLE_ADMIN`, `ROLE_MANAGER`, `ROLE_TECHNICIAN`, `ROLE_PARTS_CLERK`, `ROLE_VIEWER`) are on `TenantMembership`. The `ROLE_PERMISSIONS` dict in `app/models/user.py` maps roles to permission sets.

### Layers

- **Models** (`app/models/`) — SQLAlchemy ORM. Inherit `BaseModelMixin` (provides `save()`, `delete()`, `find_by_id()`, `find_all()`, `to_dict()`). Tenant-scoped models also inherit `TenantScopedMixin` which auto-filters queries by `g.current_tenant_id`.
- **Services** (`app/services/`) — Business logic. Instantiated fresh in views (not singletons). Includes: AuthService, NeonAuthService, OAuthService, CustomerService, JobService, BillingService, TenantService, StripeService.
- **Views** (`app/views/`) — Flask blueprints handling HTTP. Each blueprint registered at both generic prefix (`/technician`) and tenant-scoped prefix (`/org/<tenant_slug>/technician`).
- **Middleware** (`app/middleware/tenant.py`) — Resolves tenant from URL slug, session, or `X-Tenant-ID` header. Sets `g.current_tenant_id`. Exempt routes: `/auth/*`, `/static/*`, `/login`, `/logout`, `/billing/webhook`.

### Blueprints

`main_bp` (public + customers), `auth_bp` (OAuth/JWT/tenant selection), `technician_bp`, `administrator_bp`, `billing_bp` (Stripe), `onboarding_bp` (4-step flow).

### Auth & Authorization

Session-based: `session['logged_in']`, `session['user_id']`, `session['current_tenant_id']`, `session['current_role']`.

Three auth methods: traditional username/password, Google OAuth (Authlib), optional Neon Auth JWT (Better Auth).

Decorators in `app/utils/decorators.py`:
- `@login_required` — session must exist
- `@tenant_required` — requires `g.current_tenant_id`
- `@permission_required('permission_name')` — checks ROLE_PERMISSIONS
- `@role_required('role1', 'role2')` — direct role check
- `@handle_database_errors` — catches and logs DB exceptions

### Config

Classes in `config/base.py`: `BaseConfig`, `DevelopmentConfig`, `ProductionConfig`, `TestingConfig`. Selected via `FLASK_ENV` env var. `TestingConfig` uses `sqlite:///:memory:` — no PostgreSQL needed for tests. `_configure_database()` in `app/__init__.py` respects pre-set `SQLALCHEMY_DATABASE_URI` from config.

### Security

`app/utils/security.py`: `CSRFProtection` (generate/validate tokens), `PasswordSecurity` (PBKDF2 100k iterations), `InputSanitizer` (XSS prevention), `SQLInjectionProtection` (keyword scanning), `SessionSecurity` (IP validation, activity tracking), `SecurityConfig` (HSTS, X-Frame-Options headers).

### SaaS Billing

Stripe integration in `app/services/stripe_service.py`. Plans: Free, Starter ($29), Professional ($79), Enterprise ($199). 14-day trial. Webhook handler at `/billing/webhook` (no auth). Subscription model tied 1:1 to Tenant.

### Frontend

"Precision Industrial" design system: Bootstrap 5.3 + custom CSS variables (`design-system.css` + `main.css`). Colors: steel blue (#1e3a5f) + signal orange (#e85d04). Typography: DM Sans / Source Sans 3 / JetBrains Mono. Icons: Lucide (CDN). Charts: Chart.js 4.4.0. No build tools — vanilla JS + static files served by Flask.

### Database Migrations

Alembic migrations in `migrations/versions/`:
- `001` — Create multi-tenant tables (tenant, membership, subscription, inventory, inventory_transaction) + add tenant_id to existing tables
- `002` — Backfill default tenant (tenant_id=1)
- `003` — Enforce NOT NULL constraints on tenant_id, add unique constraints

## Testing Notes

- Fixtures in `tests/conftest.py`: session-scoped `app`, function-scoped `client`, `authenticated_session` (technician, tenant_id=1), `admin_session` (owner, tenant_id=1)
- Use `pytest.raises(werkzeug.exceptions.Forbidden)` instead of patching `flask.abort`
- Don't patch `builtins.len` — causes infinite recursion in Python 3.12
- Templates contain `<script>` tags; XSS tests should check for the specific payload string, not all script tags
- Available markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.security`, `@pytest.mark.slow`
- Test utilities in `tests/utils.py`: mock builders (`create_mock_customer`, `create_mock_job`, etc.), `MockDatabaseConnection`, `assert_json_response`, `generate_test_data_set`
- Coverage minimum threshold: 70%

## Key Dependencies

Flask 3.1.3, Werkzeug 3.1.6, SQLAlchemy 2.0.36, psycopg2-binary 2.9.10, Alembic 1.14.0, Authlib 1.6.6, PyJWT 2.10.1, Stripe 11.4.1, bcrypt 4.2.1, Chart.js 4.4.0, Bootstrap 5.3, Lucide Icons.
