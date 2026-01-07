# PromoPulse API

A FastAPI-based backend service for managing promotional campaigns, user subscriptions, and engagement tracking. Built as a portfolio project to demonstrate practical Python backend development skills.

## What This Project Does

This is an API for handling promotional campaigns and tracking user engagement. The main features currently implemented:

- User management with encrypted PII (email addresses)
- Database migrations that run automatically on startup
- Async database operations using SQLAlchemy
- Clean project structure with separation of concerns

The project is designed to be extended with additional features like event processing, rate limiting, and analytics.

## Tech Stack

- **Python 3.12+** with FastAPI
- **PostgreSQL** for data storage
- **SQLAlchemy** (async) for ORM
- **Alembic** for database migrations
- **Docker & Docker Compose** for containerization
- **Cryptography** (Fernet) for PII encryption

## Project Structure

```
promopulse/
├── app/
│   ├── api/              # API routes and endpoints
│   ├── core/             # Configuration and security
│   ├── db/               # Database models and migrations
│   ├── domain/           # Business logic
│   └── infrastructure/   # External services (repos, queues)
├── docker/               # Dockerfile and entrypoint script
└── tests/                # Tests
```

## Current Database Schema

- **users**: User information with encrypted email addresses
- **promotions**: Promotional campaigns with lifecycle management (draft/active/ended)
- **subscriptions**: User subscriptions to promotions with soft delete support
- **alembic_version**: Migration tracking (managed by Alembic)

## Features

### Promotions Management

The API supports managing promotional campaigns with a robust lifecycle state machine.

#### Promotion States

Promotions follow a one-way lifecycle:

```
DRAFT → ACTIVE → ENDED
```

- **DRAFT**: Initial state, all fields editable, promotion not yet live
- **ACTIVE**: Running promotion, limited editing (name/description only)
- **ENDED**: Completed promotion, read-only, no further modifications

**Important**: State transitions are manual (via API calls) and cannot be reversed. This ensures clear audit trails and prevents accidental modifications to live campaigns.

#### API Endpoints

- `POST /promotions` - Create new promotion (starts in DRAFT)
- `GET /promotions/{id}` - Get promotion by ID
- `GET /promotions?status={status}` - List promotions (filterable by status)
- `PATCH /promotions/{id}` - Update promotion fields (restrictions apply)
- `POST /promotions/{id}/status` - Change promotion status

#### Field Edit Restrictions

Different fields are editable depending on the promotion's current state:

| Status | Editable Fields |
|--------|----------------|
| DRAFT  | All fields (name, description, start_at, end_at) |
| ACTIVE | Limited (name, description only) |
| ENDED  | None (read-only) |

#### Validation Rules

- **Time Range**: `end_at` must be after `start_at`
- **State Transitions**: Must follow DRAFT → ACTIVE → ENDED (cannot skip states or move backwards)
- **Invalid Operations**: Return descriptive 422 errors with clear messages

#### Example Usage

```bash
# Create a promotion
curl -X POST http://localhost:8000/promotions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Sale",
    "description": "Get 20% off everything",
    "start_at": "2026-06-01T00:00:00Z",
    "end_at": "2026-06-30T23:59:59Z"
  }'

# List all draft promotions
curl "http://localhost:8000/promotions?status=draft"

# Activate a promotion
curl -X POST http://localhost:8000/promotions/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'

# Update description (allowed in ACTIVE state)
curl -X PATCH http://localhost:8000/promotions/1 \
  -H "Content-Type: application/json" \
  -d '{"description": "New description"}'

# End a promotion
curl -X POST http://localhost:8000/promotions/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "ended"}'
```

### Subscription Management

The API supports managing user subscriptions to active promotions with business validation rules.

#### Business Rules

- **Promotion Must Be ACTIVE**: Users can only subscribe to promotions in ACTIVE status
- **No Duplicate Subscriptions**: Each user can subscribe to a promotion only once (enforced at DB level)
- **User Must Exist**: User validation ensures referential integrity
- **Soft Delete**: Subscriptions can be deactivated (not deleted) to preserve history

#### Subscription Lifecycle

```
Active → Inactive
```

Subscriptions start as **active** (`is_active=True`) and can be deactivated (soft delete). This preserves subscription history for analytics while allowing users to unsubscribe.

#### API Endpoints

- `POST /subscriptions` - Create new subscription (201)
- `GET /subscriptions?user_id=X` - List subscriptions for a user
- `GET /subscriptions?promotion_id=Y` - List subscribers for a promotion
- `PATCH /subscriptions/{id}/deactivate` - Deactivate subscription

#### Query Parameters

The list endpoint supports flexible filtering:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | int | Yes* | Filter subscriptions by user |
| `promotion_id` | int | Yes* | Filter subscriptions by promotion |
| `is_active` | bool | No | Filter by active status (true/false) |
| `limit` | int | No | Maximum items to return (default: 100, max: 1000) |
| `offset` | int | No | Number of items to skip (default: 0) |

**Note:** Exactly ONE of `user_id` or `promotion_id` must be provided (not both, not neither).

#### Error Handling

The API returns descriptive error codes:

| Status Code | Description |
|-------------|-------------|
| 201 | Subscription created successfully |
| 404 | User or subscription not found |
| 409 | Duplicate subscription (user already subscribed) |
| 422 | Business rule violation (promotion not active, already inactive) |
| 500 | Internal server error |

#### Example Usage

```bash
# Create a subscription
curl -X POST http://localhost:8000/subscriptions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "promotion_id": 2,
    "metadata": {"source": "web", "campaign": "summer2026"}
  }'

# List all subscriptions for a user
curl "http://localhost:8000/subscriptions?user_id=1"

# List only active subscriptions for a user
curl "http://localhost:8000/subscriptions?user_id=1&is_active=true"

# List all subscribers to a promotion
curl "http://localhost:8000/subscriptions?promotion_id=2"

# List subscribers with pagination
curl "http://localhost:8000/subscriptions?promotion_id=2&limit=10&offset=20"

# Deactivate a subscription
curl -X PATCH http://localhost:8000/subscriptions/1/deactivate
```

#### Database Indexes

The subscriptions table is optimized for common query patterns:

- Single-column indexes on `user_id`, `promotion_id`, `is_active`
- Composite indexes for `(user_id, is_active)` and `(promotion_id, is_active)`
- Unique constraint on `(user_id, promotion_id)` prevents duplicates

## Getting Started

### Requirements

- Docker and Docker Compose
- That's it! Everything else runs in containers.

### Running the Application

1. **Start all services:**

```bash
docker compose up -d
```

This single command will:
- Start PostgreSQL and wait for it to be healthy
- Run all database migrations automatically
- Start the FastAPI application on port 8000

The first startup takes about 30 seconds. Subsequent restarts are faster.

2. **Check that it's running:**

```bash
docker compose ps
docker compose logs api
```

You should see messages indicating migrations completed and the API is running.

3. **Access the API:**

- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs

### Stopping the Application

```bash
docker compose down
```

To also remove the database volume (delete all data):

```bash
docker compose down -v
```

## Working with the Database

### Accessing the Database

Connect to PostgreSQL directly:

```bash
docker exec -it promopulse-db psql -U promopulse -d promopulse
```

Once connected, you can run SQL queries:

```sql
-- List all tables
\dt

-- View users (email will be encrypted)
SELECT * FROM users;

-- Check current migration version
SELECT * FROM alembic_version;
```

### Database Migrations

Migrations run automatically when the API container starts. You don't need to run them manually.

If you need to work with migrations directly:

```bash
# Check which migration version is currently applied
docker exec -it promopulse-api alembic current

# View all migrations
docker exec -it promopulse-api alembic history

# Create a new migration after changing models
docker exec -it promopulse-api alembic revision --autogenerate -m "describe your changes"

# Roll back one migration (careful with this)
docker exec -it promopulse-api alembic downgrade -1
```

## Development

### Making Code Changes

The Docker setup uses volume mounts, so code changes are reflected immediately. You don't need to rebuild the container for Python code changes.

If you change dependencies in `pyproject.toml`, rebuild:

```bash
docker compose build api
docker compose up -d
```

### Generating an Encryption Key

The application needs a Fernet encryption key for PII. Generate one:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The key is already set in `docker-compose.yml` for development. For production, use a secret management system.

### Running Tests

Tests run inside the container to match the production environment:

```bash
docker exec -it promopulse-api pytest
```

## Troubleshooting

**Container exits immediately:**

Check the logs to see what failed:

```bash
docker compose logs api
```

Common issues:
- Migration errors: Check that your database is healthy and migrations are valid
- Database not ready: The container should wait for the database automatically, but you can verify with `docker compose ps`

**Cannot connect to the database:**

Make sure the database container is running and healthy:

```bash
docker compose ps
docker compose logs db
```

**Need to start fresh:**

Delete everything and start over:

```bash
docker compose down -v
docker compose up -d
```

Note: This deletes all data in the database.

## Project Goals

This project demonstrates:

- Building a production-quality REST API with FastAPI
- Proper async database operations with SQLAlchemy
- Automated database migration handling
- Secure handling of sensitive data (PII encryption)
- Clean architecture with separation of concerns
- Containerization and easy local development setup
