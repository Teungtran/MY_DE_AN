FROM python:3.11-alpine

# Set the working directory
WORKDIR /code

# Create necessary directories
RUN mkdir -p /code/logs

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.cargo/bin/uv /usr/local/bin/uv

# Copy dependency definition
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN uv pip install --no-cache -r /code/requirements.txt --system

# Copy app code
COPY ./app /code/app
COPY ./config /code/config
COPY ./saved_models /code/saved_models

# Expose FastAPI default port
EXPOSE 8090

# Set environment variables
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]