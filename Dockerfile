# GuardBot - Production Dockerfile
FROM python:3.12-slim

# Metadata
LABEL maintainer="GuardBot Team"
LABEL version="1.0.0"
LABEL description="GuardBot - Access Control Telegram Bot"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for security
RUN groupadd -r guardbot && useradd -r -g guardbot guardbot

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p /app/data/media /app/data/export /app/logs && \
    chown -R guardbot:guardbot /app

# Switch to non-root user
USER guardbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os; os.path.exists('.bot.lock') or exit(1)"

# Run bot with start_bot.py (has lockfile protection)
CMD ["python", "start_bot.py"]
