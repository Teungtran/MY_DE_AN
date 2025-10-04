FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set the working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/app/report_agent/artifact

# Copy dependency definition first (for better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-cache-dir

COPY ./app /app/app
COPY ./config /app/config
COPY .env /app/.env

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app
# Install ODBC libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        unixodbc \
        unixodbc-dev \
        gcc \
        g++ \
        build-essential \
        curl && \
    rm -rf /var/lib/apt/lists/*
# Copy venv + app from builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/config /app/config
COPY --from=builder /app/.env /app/.env
# Ensure venv is used by default
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/app"
# Expose FastAPI default port
EXPOSE 8888

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
