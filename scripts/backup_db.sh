#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/opt/serverpulse/backups"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/serverpulse_${TIMESTAMP}.sql.gz"

docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-serverpulse}" "${POSTGRES_DB:-serverpulse}" \
  | gzip > "$BACKUP_FILE"

# Keep only the last 7 days of backups
find "$BACKUP_DIR" -name "serverpulse_*.sql.gz" -mtime +7 -delete

echo "Backup complete: $BACKUP_FILE"
