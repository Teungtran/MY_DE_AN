FROM python:3.11.9

# Set the working directory
WORKDIR /code

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.cargo/bin/uv /usr/local/bin/uv

# Copy app code
COPY ./app /code/app
COPY ./config /code/config
COPY ./logs /code/logs
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN uv pip install --no-cache -r /code/requirements.txt --system

# Expose FastAPI default port (adjust if needed)
EXPOSE 8002

# Run FastAPI using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
