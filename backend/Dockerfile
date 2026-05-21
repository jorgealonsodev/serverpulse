FROM python:3.12-slim

WORKDIR /app

# Install system deps for asyncpg and healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY alembic.ini .
COPY alembic/ alembic/
COPY app/ app/
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
