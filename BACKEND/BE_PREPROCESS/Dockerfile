FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set the working directory
WORKDIR /code

# Create necessary directories
RUN mkdir -p /code/logs

# Copy dependency definition
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache-dir


# Copy app code
COPY ./app /code/app
COPY ./config /code/config

# Expose FastAPI default port
EXPOSE 8002

# Set environment variables
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
