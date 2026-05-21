#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
MAX_RETRIES=30
RETRY_COUNT=0
while ! nc -z postgres 5432; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
        echo "ERROR: Could not connect to PostgreSQL after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "  Attempt $RETRY_COUNT/$MAX_RETRIES — retrying in 1s..."
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
cd /app && alembic upgrade head
echo "Migrations complete."

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
