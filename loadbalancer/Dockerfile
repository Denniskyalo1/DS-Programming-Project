FROM python:3.11-slim

# Install system dependencies needed for Docker-out-of-Docker management
RUN apt-get update && apt-get install -y \
    curl \
    sudo \
    && curl -fsSL https://get.docker.com | sh \
    && rm -rf /var/lib/apt/lists/*

# Grant the root container user sudo access without a password prompt
RUN echo "root ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

WORKDIR /app

# Ensure requirements file exists or install dependencies directly
RUN pip install --no-cache-dir flask requests

COPY hash_ring.py app.py ./

EXPOSE 5000

CMD ["python", "app.py"]
