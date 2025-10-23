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

# Install system dependencies and Microsoft SQL Server ODBC driver
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gnupg2 \
        software-properties-common && \
    # Add Microsoft repository
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    # Install Microsoft SQL Server ODBC driver (this will install unixodbc as dependency)
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    # Install additional build tools if needed
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy venv + app from builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/.env /app/.env

# Ensure venv is used by default
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/app"

# Expose FastAPI default port
EXPOSE 8888

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
