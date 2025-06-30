FROM python:3.11.9

# Set the working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/artifacts/data_ingestion \
    /app/artifacts/data_version \
    /app/artifacts/model_version \
    /app/artifacts/evaluation \
    /app/plots \
    /app/logs

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.cargo/bin/uv /usr/local/bin/uv

# Copy app code
COPY ./src /app/src
COPY ./controller /app/controller
COPY ./config /app/config
COPY ./main.py /app/main.py
COPY ./run_pipeline.py /app/run_pipeline.py
COPY ./requirements.txt /app/requirements.txt

# Copy .env.docker if it exists, otherwise copy .env
COPY ./.env.docker* ./.env* /app/

# Install dependencies
RUN uv pip install --no-cache -r /app/requirements.txt --system

# Expose FastAPI default port
EXPOSE 8888

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run FastAPI using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"] 