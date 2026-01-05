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
- **alembic_version**: Migration tracking (managed by Alembic)

Additional tables (promotions, subscriptions, events) are planned for future development.

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

The codebase is intentionally kept simple and well-documented to serve as a reference for backend development patterns.