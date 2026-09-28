#!/bin/bash
# روی سرور، داخل پوشهٔ پروژه، بعد از کپی فایل dump:
#   ./deploy/postgres/restore-prod.sh /path/to/management.dump
# پایگاه فعلی سرور پاک و با دادهٔ لپ‌تاپ جایگزین می‌شود.
set -euo pipefail

dump="${1:-}"
if [ -z "$dump" ] || [ ! -f "$dump" ]; then
  echo "مسیر فایل dump را بدهید" >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$root"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

user="${POSTGRES_USER:-management}"
db="${POSTGRES_DB:-management_db}"

docker compose -f docker-compose.prod.yml stop backend
docker exec -i management_postgres pg_restore \
  --clean \
  --if-exists \
  --no-owner \
  --role="$user" \
  -U "$user" \
  -d "$db" \
  < "$dump"
docker compose -f docker-compose.prod.yml start backend

echo "بازگردانی انجام شد. با حساب قبلی لپ‌تاپ وارد شوید."
