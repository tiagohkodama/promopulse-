# Multi-stage Dockerfile for PromoPulse API

##########
# Builder
##########
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build tools (needed later for DB/crypto libs)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and source code (needed for `pip install .`)
COPY pyproject.toml .
COPY README.md .
COPY promopulse ./promopulse

# Install dependencies + package into /install
RUN pip install --upgrade pip \
    && pip install --prefix=/install .

##########
# Runtime
##########
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user
RUN useradd -m appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (for runtime)
COPY promopulse ./promopulse
COPY pyproject.toml .
COPY README.md .
COPY alembic.ini .

USER appuser

EXPOSE 8000

# Start FastAPI via Uvicorn
CMD ["uvicorn", "promopulse.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
