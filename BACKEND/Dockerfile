FROM python:3.11.9

# Set the working directory
WORKDIR /code

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.cargo/bin/uv /usr/local/bin/uv

# Copy all service code
COPY ./BE_ADMIN /code/BE_ADMIN
COPY ./BE_CHATBOT /code/BE_CHATBOT
COPY ./BE_PREPROCESS /code/BE_PREPROCESS
COPY ./main.py /code/main.py

# Create logs directory
RUN mkdir -p /code/logs

# Install dependencies for all services
RUN cd /code/BE_ADMIN && uv pip install --no-cache -r requirements.txt --system
RUN cd /code/BE_CHATBOT && uv pip install --no-cache -r requirements.txt --system
RUN cd /code/BE_PREPROCESS && uv pip install --no-cache -r requirements.txt --system

# Install multiprocessing dependencies
RUN pip install uvicorn

# Expose all service ports
EXPOSE 8090 8091 8092

# Set environment variables
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1

# Run the main script that starts all services
CMD ["python", "main.py"] 