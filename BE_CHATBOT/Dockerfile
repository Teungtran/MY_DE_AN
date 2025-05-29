FROM python:3.11.9

# Set the working directory
WORKDIR /code

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.cargo/bin/uv /usr/local/bin/uv

# Copy application code and requirements
COPY ./app /code/app
COPY ./config /code/config
COPY ./logs /code/logs
COPY ./requirements.txt /code/requirements.txt

# Install Python dependencies
RUN uv pip install --no-cache -r /code/requirements.txt --system

# Expose the internal port (FastAPI)
EXPOSE 8090

#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]