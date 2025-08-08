FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set the working directory
WORKDIR /code

# Create necessary directories
RUN mkdir -p /code/logs /code/app/report_agent/artifact

# Copy dependency definition first (for better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-cache-dir

# Copy app code and config
COPY ./app /code/app
COPY ./config /code/config

# Expose FastAPI default port
EXPOSE 8888

# Set environment variables
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1

# Run FastAPI using uvicorn with the uv environment
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
