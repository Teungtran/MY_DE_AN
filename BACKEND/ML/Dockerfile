FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set the working directory
WORKDIR /code

# Create necessary directories
RUN mkdir -p /app/artifacts/data_ingestion \
    /app/artifacts/data_version \
    /app/artifacts/model_version \
    /app/artifacts/evaluation \
    /app/plots \
    /app/logs

# Copy dependency definition
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache-dir

# Copy app code
COPY ./src /code/src
COPY ./controller /code/controller
COPY ./config /code/config
COPY ./main.py /code/main.py
COPY ./run_pipeline.py /code/run_pipeline.py

# Expose FastAPI default port
EXPOSE 8888

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run FastAPI using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"] 