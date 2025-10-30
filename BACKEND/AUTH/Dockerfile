FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set the working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs

# Copy dependency definition
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache-dir

# Copy app code (includes utils and config subdirectories)
COPY app/ ./app/
# Copy environment file
COPY .env ./

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Copy venv + app from builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/.env /app/.env

# Ensure venv is used by default
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/app"
# Set SQLite database path to shared volume
ENV SQLITE_DB_PATH="/app/data/auth.db"

# Expose FastAPI default port
EXPOSE 8888

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
