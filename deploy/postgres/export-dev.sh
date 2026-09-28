#!/bin/bash
# از لپ‌تاپ: نسخهٔ باینری پایگاه محلی (پورت 5437) را می‌گیرد.
set -euo pipefail

root="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "$root/deploy/postgres/backups"
out="${1:-$root/deploy/postgres/backups/management_$(date +%Y%m%d_%H%M%S).dump}"

export PGPASSWORD="${POSTGRES_PASSWORD:-management}"
pg_dump \
  -h 127.0.0.1 \
  -p "${POSTGRES_PORT:-5437}" \
  -U "${POSTGRES_USER:-management}" \
  -d "${POSTGRES_DB:-management_db}" \
  -Fc \
  -f "$out"

echo "$out"
