# Neon Better Auth + Flask Integration Guide

> A battle-tested guide for integrating [Neon Auth](https://neon.tech/docs/guides/neon-auth) (powered by [Better Auth](https://www.better-auth.com/)) with a Flask application. This document captures every pitfall encountered during a production deployment and how to solve them.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Configuration](#configuration)
4. [Client-Side Integration](#client-side-integration)
5. [Server-Side Integration](#server-side-integration)
6. [Authentication Flows](#authentication-flows)
7. [Multi-Tenant Post-Auth Routing](#multi-tenant-post-auth-routing)
8. [Pitfalls & Lessons Learned](#pitfalls--lessons-learned)
9. [Debugging Checklist](#debugging-checklist)
10. [File Reference](#file-reference)

---

## Architecture Overview

```
Browser (login page)
   |
   |  1. User enters credentials or clicks "Google Sign In"
   v
Neon Auth Server (Better Auth REST API)
   |
   |  2. Returns session token (opaque, NOT always a JWT)
   v
Browser (neon-auth.js)
   |
   |  3. POSTs token + user data to Flask backend
   v
Flask Backend (/auth/neon-callback)
   |
   |  4. Validates token via multiple strategies
   |  5. Establishes Flask session
   v
Dashboard / Tenant Selection / Organization Registration
```

**Key architectural insight:** Neon Auth runs on its own domain. It sets session cookies on *its* domain, which means your Flask server **cannot read those cookies directly**. All tokens must be explicitly passed from the client to Flask via request bodies.

---

## Prerequisites

- Python 3.12+ with Flask 3.x
- PostgreSQL database (Neon) with the `neon_auth` schema enabled
- A Neon Auth project configured in the Neon Console
- PyJWT and cryptography packages for JWKS verification

```
pip install flask flask-sqlalchemy pyjwt requests cryptography
```

### Neon Console Setup

1. Enable **Neon Auth** in your Neon project
2. Configure authentication methods (email/password, Google OAuth, etc.)
3. **Add your production domain to Trusted Origins** (e.g., `https://yourdomain.com`)
4. Note your **Neon Auth URL** (e.g., `https://auth.xxxx.neon.tech`)

> **CRITICAL:** If you skip step 3, all browser-to-Neon-Auth requests will fail with `Invalid origin`. This is the most commonly missed step.

---

## Configuration

### Environment Variables

```bash
NEON_AUTH_URL=https://auth.xxxx.neon.tech    # Your Neon Auth endpoint
DATABASE_URL=postgresql://...                 # Must be on the same Neon project
```

### Flask Config

```python
# config/base.py
class BaseConfig:
    NEON_AUTH_URL = os.environ.get('NEON_AUTH_URL', '')
    NEON_AUTH_JWKS_URL = os.environ.get('NEON_AUTH_JWKS_URL', '')  # Optional override
```

### HTML Meta Tag

Your base layout must expose the Neon Auth URL to client-side JavaScript:

```html
<!-- base/layout.html -->
<head>
    <meta name="neon-auth-url" content="{{ config.get('NEON_AUTH_URL') }}">
</head>
```

---

## Client-Side Integration

### Script Loading

Load your auth client script **once** in the base layout, with a cache-busting parameter:

```html
<!-- base/layout.html -->
<script src="{{ url_for('static', filename='js/neon-auth.js') }}?v={{ cache_version }}"></script>
```

> **Pitfall #1: Duplicate script loading.** If you load `neon-auth.js` in both your base layout AND in a page-specific `{% block extra_js %}`, you will get `Identifier 'NeonAuthClient' has already been declared`. Only load it once in the base layout.

> **Pitfall #2: Browser caching.** During active development, always use a cache-busting query parameter (`?v=timestamp`). Without it, browsers may serve stale JavaScript for hours even after deploying fixes.

### NeonAuthClient Class

The client-side class wraps the Neon Auth REST API:

```javascript
class NeonAuthClient {
    constructor(authUrl) {
        this.authUrl = authUrl.replace(/\/$/, '');
    }

    async signInWithEmailPassword(email, password) {
        const response = await fetch(`${this.authUrl}/sign-in/email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
            credentials: 'include'  // REQUIRED for cross-origin cookies
        });
        // ...
    }
}
```

**The `credentials: 'include'` option is mandatory** on every fetch to Neon Auth. Without it, the browser will not send/receive cookies from the Neon Auth domain.

### Passing Tokens to Flask

After authenticating with Neon Auth, you **must** explicitly pass the token to your Flask backend. Do NOT rely on cookies:

```javascript
// After successful Neon Auth sign-in
const signInData = await response.json();

// Extract token - check multiple locations
const token = signInData.token
    || (signInData.session && signInData.session.token)
    || null;

// POST to Flask backend with token AND user data
const callbackResponse = await fetch('/auth/neon-callback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        token: token,
        user: signInData.user || null  // Fallback user data
    }),
    credentials: 'include'
});
```

> **Pitfall #3: Token location varies.** Better Auth may return the token at `data.token`, `data.session.token`, or neither. Always check multiple locations. If no token is found, call the `get-session` endpoint as a fallback.

### Handling Google OAuth Redirects

After Google OAuth, Neon Auth redirects back to your app with a `neon_auth_session_verifier` query parameter. You need to detect this on **every page** (not just the callback URL):

```javascript
// Run on every page load
function checkSessionVerifier() {
    const params = new URLSearchParams(window.location.search);
    const verifier = params.get('neon_auth_session_verifier');

    if (!verifier) return;

    // Fetch session from Neon Auth (client-side cookies are accessible)
    const sessionData = await fetch(`${this.authUrl}/get-session`, {
        credentials: 'include'
    }).then(r => r.json());

    // Forward to Flask
    await fetch('/auth/neon-callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            token: sessionData.session?.token,
            user: sessionData.user
        }),
        credentials: 'include'
    });
}
```

> **Pitfall #4: OAuth redirect URL.** Neon Auth may redirect to your root URL (`/?neon_auth_session_verifier=...`) rather than a dedicated callback path. Your session verifier detection must run on every page, not just `/auth/callback`.

---

## Server-Side Integration

### Token Validation Strategies

Better Auth can issue **opaque session tokens** (short random strings), not just JWTs. Your backend must handle both:

```python
class NeonAuthService:
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Try JWT first, fall back to opaque token validation"""
        # Strategy 1: JWT verification via JWKS
        payload = self.verify_token(token)

        if not payload:
            # Strategy 2: Opaque token validation
            payload = self.validate_session_token(token)
            if not payload:
                return None
            # CRITICAL: Rollback any dirty DB state from failed lookups
            try:
                db.session.rollback()
            except Exception:
                pass

        return User.authenticate_with_jwt(payload)
```

### Opaque Token Validation (4 Strategies)

When JWT verification fails, try these strategies in order:

```python
def validate_session_token(self, token: str) -> Optional[dict]:
    # Strategy 1: Pass token as cookie to Neon Auth get-session API
    response = requests.get(
        f"{auth_url}/get-session",
        headers={'Cookie': f'better-auth.session_token={token}'},
        timeout=10
    )

    # Strategy 2: Pass token as Bearer header
    response = requests.get(
        f"{auth_url}/get-session",
        headers={'Authorization': f'Bearer {token}'},
        timeout=10
    )

    # Strategy 3: Direct DB lookup (plain token)
    result = db.session.execute(
        text("SELECT ... FROM neon_auth.session WHERE token = :token"),
        {'token': token}
    )

    # Strategy 4: DB lookup with SHA-256 hashed token
    hashed = hashlib.sha256(token.encode('utf-8')).hexdigest()
    result = db.session.execute(
        text("SELECT ... FROM neon_auth.session WHERE token = :token"),
        {'token': hashed}
    )
```

> **Pitfall #5: Better Auth stores hashed tokens.** The `neon_auth.session` table stores **SHA-256 hashed** session tokens, not plain text. A plain token lookup will always return no results. You must hash the token before querying the database.

### Handling neon_auth Schema Column Names

Better Auth's database schema uses different column naming conventions depending on the ORM adapter (Drizzle uses camelCase, Prisma uses snake_case). Your queries must try multiple conventions:

```python
# camelCase (Drizzle ORM default)
"""SELECT u.id, u.email, u.name, u."emailVerified"
   FROM neon_auth.session s
   JOIN neon_auth."user" u ON s."userId" = u.id
   WHERE s.token = :token AND s."expiresAt" > NOW()"""

# snake_case (Prisma)
"""SELECT u.id, u.email, u.name, u.email_verified
   FROM neon_auth.session s
   JOIN neon_auth."user" u ON s.user_id = u.id
   WHERE s.token = :token AND s.expires_at > NOW()"""

# all lowercase (PostgreSQL unquoted default)
"""SELECT u.id, u.email, u.name, u.emailverified
   FROM neon_auth.session s
   JOIN neon_auth."user" u ON s.userid = u.id
   WHERE s.token = :token AND s.expiresat > NOW()"""
```

> **Pitfall #6: PostgreSQL transaction poisoning.** When a SQL query fails (e.g., column `expiresAt` doesn't exist), PostgreSQL puts the connection into `InFailedSqlTransaction` state. **ALL subsequent queries will fail** until you call `db.session.rollback()`. You MUST rollback after each failed query attempt.

```python
for query_sql in [camelcase_query, snake_case_query, lowercase_query]:
    try:
        result = db.session.execute(text(query_sql), {'token': token})
        if result:
            return parse_result(result)
    except Exception:
        # CRITICAL: Rollback to prevent transaction poisoning
        try:
            db.session.rollback()
        except Exception:
            pass
        continue
```

### UUID vs String Type Mismatch

The `neon_auth.user.id` column is a PostgreSQL `UUID` type. If your application's `User` model stores `neon_auth_user_id` as `VARCHAR`, you must cast the value to `str` before comparing:

```python
@classmethod
def find_by_neon_auth_id(cls, neon_auth_user_id: str):
    # CRITICAL: Cast to str to prevent "operator does not exist: character varying = uuid"
    neon_auth_user_id = str(neon_auth_user_id)
    return db.session.execute(
        db.select(cls).where(cls.neon_auth_user_id == neon_auth_user_id)
    ).scalar_one_or_none()
```

> **Pitfall #7: UUID type mismatch.** The `neon_auth` schema returns UUID objects from PostgreSQL. If you pass these directly to a query comparing against a VARCHAR column, PostgreSQL throws `operator does not exist: character varying = uuid`. Always cast to `str()`.

### Parsing Neon Auth API Responses

The `get-session` endpoint may return `null` instead of `{}` for invalid sessions:

```python
def _parse_session_response(self, response):
    if not response.ok:
        return None
    try:
        data = response.json()
    except Exception:
        return None

    # CRITICAL: data can be None (JSON "null"), not just an empty dict
    if not data or not isinstance(data, dict):
        return None

    user_data = data.get('user')
    if not user_data:
        return None

    # Always cast sub to str (may be UUID object)
    user_id = user_data.get('id')
    return {
        'sub': str(user_id) if user_id else None,
        'email': user_data.get('email'),
        'name': user_data.get('name'),
        'email_verified': user_data.get('emailVerified',
                            user_data.get('email_verified', False)),
    }
```

> **Pitfall #8: Null JSON body.** Neon Auth returns HTTP 200 with body `null` for some invalid session requests. `response.json()` returns Python `None`, and `None.get('user')` raises `AttributeError`. Always check for `None` before accessing dict methods.

### Flask Callback Endpoint

The main callback endpoint should accept tokens from the request body and include a client-data fallback:

```python
@auth_bp.route('/neon-callback', methods=['POST'])
def neon_callback():
    body = request.get_json(silent=True) or {}

    # 1. Get token from body (preferred) or cookie (fallback)
    session_token = body.get('token') or request.cookies.get('better-auth.session_token')

    if not session_token:
        return jsonify({'error': 'No session token'}), 401

    # 2. Validate token and get user
    auth_service = AuthService()
    user = auth_service.authenticate_jwt(session_token)

    # 3. Fallback: use client-provided user data
    if not user:
        client_user = body.get('user')
        if client_user and client_user.get('id') and client_user.get('email'):
            try:
                db.session.rollback()  # Clean up any dirty transaction
            except Exception:
                pass
            user = User.authenticate_with_jwt({
                'sub': client_user['id'],
                'email': client_user['email'],
                'name': client_user.get('name', ''),
                'email_verified': client_user.get('emailVerified', False),
            })

    if user:
        auth_service.establish_session(user)
        redirect_url = auth_service.resolve_post_auth_redirect(user.user_id)
        return jsonify({'success': True, 'redirect': redirect_url})

    return jsonify({'error': 'Invalid session'}), 401
```

### Proxying Neon Auth Endpoints

To avoid CORS issues, proxy email verification and password reset through Flask:

```python
@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """Proxy email OTP verification to Neon Auth"""
    data = request.get_json()
    response = requests.post(
        f"{neon_auth_url}/email-otp/verify-email",
        json={'email': data['email'], 'otp': data['otp']},
        timeout=10
    )
    return jsonify(response.json()), response.status_code


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Proxy forgot-password to Neon Auth"""
    data = request.get_json(silent=True) or {}
    response = requests.post(
        f"{neon_auth_url}/forget-password/email",
        json={'email': data['email']},
        timeout=10
    )
    return jsonify(response.json()), response.status_code
```

---

## Authentication Flows

### Email/Password Sign-In

```
User                Browser (JS)           Neon Auth            Flask
 |                      |                      |                  |
 |  Enter credentials   |                      |                  |
 |--------------------->|                      |                  |
 |                      |  POST /sign-in/email |                  |
 |                      |--------------------->|                  |
 |                      |  { token, user }     |                  |
 |                      |<---------------------|                  |
 |                      |                      |                  |
 |                      |  POST /auth/neon-callback               |
 |                      |  { token, user }     |                  |
 |                      |---------------------------------------->|
 |                      |                      |  validate token  |
 |                      |                      |  establish session|
 |                      |  { redirect: "/dashboard" }             |
 |                      |<----------------------------------------|
 |  Redirect            |                      |                  |
 |<---------------------|                      |                  |
```

### Google OAuth

```
User                Browser (JS)           Neon Auth            Flask
 |                      |                      |                  |
 |  Click "Google"      |                      |                  |
 |--------------------->|                      |                  |
 |                      | POST /sign-in/social |                  |
 |                      |--------------------->|                  |
 |                      |  { url: google... }  |                  |
 |                      |<---------------------|                  |
 |  Redirect to Google  |                      |                  |
 |<---------------------|                      |                  |
 |                      |                      |                  |
 |  (Google auth)       |                      |                  |
 |  Redirect back       |                      |                  |
 |----> /?neon_auth_session_verifier=xxx       |                  |
 |                      |                      |                  |
 |       (or)           |                      |                  |
 |----> /auth/callback?neon_auth_session_verifier=xxx             |
 |                      |                      |                  |
 |                      |  GET /get-session    |                  |
 |                      |--------------------->|                  |
 |                      |  { session, user }   |                  |
 |                      |<---------------------|                  |
 |                      |                      |                  |
 |                      |  POST /auth/neon-callback               |
 |                      |  { token, user }                        |
 |                      |---------------------------------------->|
 |                      |  { redirect: "/dashboard" }             |
 |                      |<----------------------------------------|
 |  Redirect            |                      |                  |
 |<---------------------|                      |                  |
```

### Email Sign-Up with OTP Verification

```
User                Browser (JS)           Neon Auth            Flask
 |                      |                      |                  |
 |  Submit signup form  |                      |                  |
 |--------------------->|                      |                  |
 |                      | POST /sign-up/email  |                  |
 |                      |--------------------->|                  |
 |                      |  (sends OTP email)   |                  |
 |                      |<---------------------|                  |
 |                      |                      |                  |
 |  Show OTP overlay    |                      |                  |
 |<---------------------|                      |                  |
 |                      |                      |                  |
 |  Enter 6-digit OTP   |                      |                  |
 |--------------------->|                      |                  |
 |                      | POST /auth/verify-email (proxied)       |
 |                      |---------------------------------------->|
 |                      |              POST /email-otp/verify-email|
 |                      |                      |<-----------------|
 |                      |                      |  { success }     |
 |                      |                      |----------------->|
 |                      |  { success }         |                  |
 |                      |<----------------------------------------|
 |                      |                      |                  |
 |                      |  GET /get-session    |                  |
 |                      |--------------------->|                  |
 |                      |  { session, user }   |                  |
 |                      |<---------------------|                  |
 |                      |                      |                  |
 |                      |  POST /auth/neon-callback               |
 |                      |  { token, user }                        |
 |                      |---------------------------------------->|
 |                      |  { redirect }                           |
 |                      |<----------------------------------------|
```

---

## Multi-Tenant Post-Auth Routing

After authentication, route users based on their tenant memberships:

```python
def resolve_post_auth_redirect(self, user_id: int) -> str:
    memberships = self._get_user_memberships(user_id)

    if not memberships:
        # New user, no organization yet
        return url_for('auth.no_organization')

    if len(memberships) == 1:
        # Auto-select single tenant
        self.establish_tenant_session(user_id, memberships[0]['tenant_id'])
        return url_for('main.dashboard')

    # Multiple tenants - try default, then show picker
    default = next((m for m in memberships if m['is_default']), None)
    if default:
        self.establish_tenant_session(user_id, default['tenant_id'])
        return url_for('main.dashboard')

    return url_for('auth.select_tenant')
```

**Required pages:**
- `/auth/no-organization` - Shown when user has no tenant memberships
- `/auth/register-organization` - Form to create a new tenant
- `/auth/select-tenant` - Picker when user belongs to multiple tenants

---

## Pitfalls & Lessons Learned

### Summary Table

| # | Pitfall | Symptom | Solution |
|---|---------|---------|----------|
| 1 | Duplicate script loading | `Identifier already declared` | Load neon-auth.js only once in base layout |
| 2 | Browser caching | Old JS served after deploy | Add `?v=timestamp` cache-busting param |
| 3 | Token location varies | Token undefined | Check `data.token`, `data.session.token`, then `getSession()` |
| 4 | OAuth redirect to root URL | Homepage shown with verifier param | Detect `neon_auth_session_verifier` on every page |
| 5 | Hashed tokens in DB | DB lookup returns no results | Hash token with SHA-256 before querying |
| 6 | PostgreSQL transaction poisoning | `InFailedSqlTransaction` on all queries | `db.session.rollback()` after each failed SQL attempt |
| 7 | UUID vs VARCHAR mismatch | `operator does not exist: varchar = uuid` | Cast `neon_auth_user_id` to `str()` before queries |
| 8 | Null JSON body from API | `AttributeError: NoneType has no attribute get` | Check `if not data or not isinstance(data, dict)` |
| 9 | Cross-origin cookies invisible | Flask can't read Neon Auth cookies | Pass tokens in request body, not cookies |
| 10 | Chart.js ESM vs UMD | `Cannot use import statement outside a module` | Use `chart.umd.min.js` (not `chart.min.js`) |
| 11 | Neon Auth trusted origins | `Invalid origin` error | Add your domain to Neon Console trusted origins |
| 12 | Missing templates | 500 Internal Server Error | Create all templates referenced in route handlers |
| 13 | Column naming conventions | SQL errors on neon_auth schema queries | Try camelCase, snake_case, and lowercase variants |

### Detailed Lessons

#### Cross-Origin Cookie Invisibility (The Fundamental Problem)

This is the single most important thing to understand: **Neon Auth's session cookies live on Neon Auth's domain, not yours.** Your Flask backend on `yourdomain.com` will **never** see a cookie set by `auth.xxxx.neon.tech`.

The solution is a two-step dance:
1. Client-side JavaScript can access Neon Auth cookies (via `credentials: 'include'`)
2. Client reads the session/token from Neon Auth, then POSTs it to your Flask backend

This is why you need the `neon-auth.js` client library on every page.

#### PostgreSQL Transaction Poisoning (The Silent Killer)

This bug is particularly insidious because it causes cascading failures that appear unrelated to the root cause. When you try multiple SQL queries against the `neon_auth` schema and one fails (e.g., wrong column name), PostgreSQL enters a failed transaction state. Every subsequent query on that connection will fail with:

```
psycopg2.errors.InFailedSqlTransaction: current transaction is aborted,
commands ignored until end of transaction block
```

**The fix:** Call `db.session.rollback()` after ANY potentially-failing database query, especially when trying multiple schema variants. Also rollback after `validate_session_token()` returns, before performing any `User` model queries.

#### Better Auth Token Format

Better Auth does NOT always issue JWTs. It often issues **opaque session tokens** - short random strings (32 characters) that are not self-verifiable. Your backend must support both:

1. **JWT path:** Fetch JWKS from `/.well-known/jwks.json`, verify signature
2. **Opaque path:** Call Neon Auth's `get-session` API or query the DB directly

When querying the database directly, remember that Better Auth stores tokens as SHA-256 hashes:

```python
import hashlib
hashed_token = hashlib.sha256(token.encode('utf-8')).hexdigest()
```

---

## Debugging Checklist

When authentication fails, check these in order:

1. **Browser Console:** Any JavaScript errors? Is `window.neonAuth` defined?
2. **Network Tab:** What does the Neon Auth sign-in response look like? Is there a `token` field?
3. **`/auth/neon-callback` response:** Check the debug info in the JSON response
4. **Server logs:** Look for the validation strategy results:
   - `jwt_valid: true/false`
   - `opaque_valid: true/false`
   - `DB plain lookup SUCCESS/failed`
   - `DB hashed lookup SUCCESS/failed`
5. **Transaction state:** Look for `InFailedSqlTransaction` - indicates a missing rollback
6. **Type errors:** Look for `character varying = uuid` - indicates missing `str()` cast
7. **Neon Console:** Is your domain in the trusted origins list?
8. **Cache:** Force-refresh the page (`Ctrl+Shift+R`) to bypass cached JavaScript

### Adding a Debug Panel

During development, a floating debug panel is invaluable. Add one to your auth client:

```javascript
class NeonAuthClient {
    _addDebugLog(message) {
        const panel = document.getElementById('neonAuthDebugPanel');
        if (!panel) this._createDebugPanel();
        const entry = document.createElement('div');
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        panel.querySelector('.logs').appendChild(entry);
    }
}
```

Include a "Copy All Logs" button so users can easily share diagnostics. Remove the debug panel before production release.

---

## File Reference

| File | Purpose |
|------|---------|
| `app/static/js/neon-auth.js` | Client-side Neon Auth SDK wrapper |
| `app/services/auth_service.py` | Server-side token validation and session management |
| `app/views/auth.py` | Flask routes for all auth endpoints |
| `app/models/user.py` | User model with `authenticate_with_jwt()` |
| `app/templates/auth/login.html` | Sign-in/sign-up page with OTP verification |
| `app/templates/auth/oauth_completing.html` | OAuth bridge page for cross-origin token passing |
| `app/templates/auth/no_organization.html` | Shown when user has no tenant memberships |
| `app/templates/auth/register_organization.html` | Organization creation form |
| `app/templates/auth/select_tenant.html` | Multi-tenant picker |
| `app/templates/auth/verify_email.html` | Standalone email verification page |
| `app/templates/base/layout.html` | Base template with Neon Auth meta tag and script |
| `config/base.py` | Flask configuration with NEON_AUTH_URL |

---

## Version History

- **2026-02-21:** Initial guide based on production deployment of RepairOS
- Covers Neon Auth (Better Auth) integration with Flask + multi-tenant architecture
- Tested with: Flask 3.1.3, SQLAlchemy 2.0.36, PyJWT 2.10.1, PostgreSQL (Neon), Python 3.12
