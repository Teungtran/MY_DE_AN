FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set the working directory
WORKDIR /app


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
COPY ./src /app/src
COPY ./controller /app/controller
COPY ./config /app/config
COPY ./utils /app/utils
COPY ./main.py /app/main.py
COPY ./dvc.yaml /app/dvc.yaml


FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Copy venv + app from builder stage
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/controller /app/controller
COPY --from=builder /app/config /app/config
COPY --from=builder /app/utils /app/utils
COPY --from=builder /app/main.py /app/main.py
COPY --from=builder /app/dvc.yaml /app/dvc.yaml

# Ensure venv is used by default
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/src"
# Expose FastAPI default port
EXPOSE 8888

# Run FastAPI using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"]

