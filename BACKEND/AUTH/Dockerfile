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
COPY ./start.sh /code/start.sh

RUN chmod +x /code/start.sh
# Expose FastAPI default port
EXPOSE 8888
# Set environment variables
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1

# Run FastAPI using uvicorn
CMD ["/code/start.sh"]

