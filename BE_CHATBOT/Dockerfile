FROM python:3.11-slim

WORKDIR /app


# Install dependencies and update CA certificates
RUN echo -n | openssl s_client -showcerts -connect files.pythonhosted.org:443 \
    | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' > pythonhosted.crt
RUN cp pythonhosted.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt


# Install Poetry
RUN python -m ensurepip --upgrade && \
    pip install --no-cache-dir --upgrade pip && \
    pip install poetry

# Copy the Poetry configuration files
COPY pyproject.toml /app/

# Install the project dependencies using Poetry
RUN poetry install --no-root

# Copy the application code into the container
COPY config /config
COPY app /app

# Expose the port that FastAPI will run on
EXPOSE 8090

COPY scripts/start.sh .
RUN chmod +x start.sh
# Set the command to run your FastAPI app using Uvicorn
CMD ["./start.sh"]