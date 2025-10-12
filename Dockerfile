# Gmail Digest Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY config.yml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create directory for logs
RUN mkdir -p /app/logs

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set timezone (will be overridden by env var)
ENV TZ=America/New_York

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["cron"]

