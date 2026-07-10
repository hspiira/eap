#!/usr/bin/env bash
# Database backup script for Evexía EAP.
# Usage: set DATABASE_URL in the environment, then run:
#   ./scripts/backup_db.sh [OUTPUT_DIR]
# Example (cron, daily at 02:00): 0 2 * * * DATABASE_URL='...' /path/to/eap/scripts/backup_db.sh /backups
# See docs/BACKUP_AND_RECOVERY.md for restore and retention.

set -euo pipefail

OUTPUT_DIR="${1:-./backups}"
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set." >&2
  exit 1
fi

if [[ "$DATABASE_URL" == sqlite* ]]; then
  # SQLite: extract path (e.g. sqlite+aiosqlite:///./evexia.db -> ./evexia.db)
  DB_PATH="${DATABASE_URL#*:///}"
  DB_PATH="${DB_PATH#*://}"   # in case of three slashes
  if [[ ! -f "$DB_PATH" ]]; then
    echo "ERROR: SQLite file not found: $DB_PATH" >&2
    exit 1
  fi
  BACKUP_FILE="$OUTPUT_DIR/evexia_sqlite_${TIMESTAMP}.db"
  sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'" 2>/dev/null || cp "$DB_PATH" "$BACKUP_FILE"
  echo "Backup written: $BACKUP_FILE"
elif [[ "$DATABASE_URL" == postgresql* ]] || [[ "$DATABASE_URL" == postgres* ]]; then
  # PostgreSQL: use pg_dump (logical backup). pg_dump expects postgresql:// (no +asyncpg).
  PG_URL="${DATABASE_URL/+asyncpg/}"
  BACKUP_FILE="$OUTPUT_DIR/evexia_pg_${TIMESTAMP}.dump"
  pg_dump -Fc "$PG_URL" -f "$BACKUP_FILE"
  echo "Backup written: $BACKUP_FILE"
else
  echo "ERROR: Unsupported DATABASE_URL scheme. Supported: sqlite, postgresql." >&2
  exit 1
fi
