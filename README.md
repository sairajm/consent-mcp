# consent-mcp: The Public Consent Handshake for AI Agents

![CI Status](https://github.com/sairajm/consent-mcp/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)

> **"Measure Twice, Cut Once."**

**consent-mcp** is an open-source Model Context Protocol (MCP) server that acts as an ethical gateway for proactive AI agents. It ensures that no autonomous agent initiates contact with a human target (neighbor, patient, or community member) without an explicit, verified consent handshake.

## 🚀 Why This Exists

We are moving from "Chatbots" (reactive) to "Agents" (proactive).

- **The Problem:** A proactive agent checking on a neighbor can quickly become a nuisance or a privacy violation if it lacks social awareness.
- **The Solution:** This tool provides a **Blocking Mechanism**. Agents must call `check_consent` before performing any task. If consent is not `GRANTED`, the agent is hard-blocked at the tool level.

## ✨ Features

- **Double-Opt-In Workflow:** Sends SMS (via Twilio) or email (via SendGrid) to the target requesting permission
- **Blocking Tool:** `check_consent` returns `False` unless consent is valid and unexpired
- **Requester Tracking:** Multiple users can request consent from the same target independently
- **Consent Expiration:** All consent has an expiration date for security
- **Audit Logging:** Every request, grant, and revocation is logged to PostgreSQL
- **Pluggable Auth:** API key or OAuth authentication out of the box
- **Domain Driven Design:** Clean architecture with swappable infrastructure
- **Docker Ready:** Deploy with a single `docker-compose up`

## 📦 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/sairajm/consent-mcp.git
cd consent-mcp

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# At minimum, set API_KEYS for authentication

# Start the server
docker-compose up --build
```

### Local Development

### Local Development (Recommended)
This workflow runs PostgreSQL in Docker but executes the Python server locally on your machine for fast iteration.

1.  **Windows**:
    ```powershell
    .\scripts\start_local.ps1
    ```

2.  **Linux/Mac**:
    ```bash
    chmod +x scripts/start_local.sh
    ./scripts/start_local.sh
    ```

This script will:
- Check for `.env` (copying from `.env.example` if needed).
- Start a specific local Postgres container (`consent-mcp-postgres-dev`).
- Wait for the database to be ready.
- Run database migrations.
- Start the MCP server with the local environment configuration.

> **Note**: For manual setup, see `.github/workflows/ci.yml`.

## 🔧 Configuration

All configuration is via environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `ENV` | No | Environment: `test`, `development`, `production` (default: `development`) |
| `DATABASE_URL` | Yes | PostgreSQL connection URL |
| `AUTH_PROVIDER` | No | Auth method: `api_key`, `oauth`, `none` (default: `api_key`) |
| `API_KEYS` | For api_key auth | Comma-separated `key:client_id` pairs |
| `TWILIO_ACCOUNT_SID` | For SMS | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | For SMS | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | For SMS | Twilio phone number (E.164 format) |
| `SENDGRID_API_KEY` | For email | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | For email | Sender email address |

## 🛠️ MCP Tools

### SMS Tools

#### `request_consent_sms`
Request consent from a target via SMS.

```json
{
  "requester_phone": "+15551234567",
  "requester_name": "Alice",
  "target_phone": "+15559876543",
  "target_name": "Bob",
  "scope": "wellness_check",
  "expires_in_days": 30
}
```

#### `check_consent_sms`
**BLOCKING:** Check if requester has active consent to contact target.

```json
{
  "requester_phone": "+15551234567",
  "target_phone": "+15559876543"
}
```

Returns `true` ONLY if consent is `GRANTED` and not expired.

### Email Tools

#### `request_consent_email`
Request consent from a target via email.

```json
{
  "requester_email": "alice@example.com",
  "requester_name": "Alice",
  "target_email": "bob@example.com",
  "target_name": "Bob",
  "scope": "appointment_reminder",
  "expires_in_days": 365
}
```

#### `check_consent_email`
**BLOCKING:** Check if requester has active consent to contact target via email.

### Admin Tools (Test Environment Only)

#### `admin_simulate_response`
Simulate a consent response for testing without real SMS/email.

```json
{
  "target_contact_type": "phone",
  "target_contact_value": "+15559876543",
  "requester_contact_value": "+15551234567",
  "response": "YES"
}
```

> ⚠️ This tool is only available when `ENV=test`

## 🏗️ Architecture

The project follows Domain Driven Design:

```
src/consent_mcp/
├── domain/           # Business logic (entities, services, interfaces)
├── infrastructure/   # External integrations (database, providers, auth)
└── mcp/v1/          # MCP layer (tools, request/response schemas)
```

### Extending the System

**Add a new messaging provider:**
1. Create a class implementing `IMessageProvider` in `infrastructure/providers/`
2. Register it in `infrastructure/providers/factory.py`

**Add a new auth provider:**
1. Create a class implementing `IAuthProvider` in `infrastructure/auth/`
2. Register it in `infrastructure/auth/factory.py`

**Switch databases:**
1. Create a new class implementing `IConsentRepository`
2. No changes needed in domain or MCP layers

## 🧪 Testing

```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=consent_mcp --cov-report=html

# Run specific test file
pytest tests/domain/test_services.py -v
```

## 📝 Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 🔒 Security

- All MCP requests require authentication (API key or OAuth)
- Admin tools are disabled in production
- Secrets are never logged
- Docker runs as non-root user
- Pre-commit hooks detect secrets before commit

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Install pre-commit hooks: `pre-commit install`
4. Make your changes
5. Run tests: `pytest`
6. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
