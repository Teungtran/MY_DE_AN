FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set the working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs


# Copy dependency definition
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache-dir


COPY ./app /app/app
COPY ./config /app/config

# Make start script executable
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Copy venv + app from builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/config /app/config
# Ensure venv is used by default
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/app"
# Expose FastAPI default port
EXPOSE 8888

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
