FROM python:3.11.9

# Set the working directory
WORKDIR /code

# Create necessary directories
RUN mkdir -p /code/app /code/config /code/logs

# Copy application code and requirements
COPY ./app /code/app
COPY ./config /code/config
COPY ./requirements.txt /code/requirements.txt
COPY ./saved_models /code/saved_models
# Create empty logs directory if it doesn't exist locally
RUN mkdir -p /code/logs

# Copy .env.docker if it exists, otherwise copy .env
COPY ./.env.docker* ./.env* /code/

# Install uv via pip
RUN pip install --no-cache-dir uv

# Install dependencies with uv
RUN uv pip install --no-cache -r /code/requirements.txt

# Expose the internal port (FastAPI)
EXPOSE 8090

# Set environment variable to ensure FastAPI runs in production mode
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]