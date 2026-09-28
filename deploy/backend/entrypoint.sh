#!/bin/sh
set -eu

mkdir -p /app/stt/media
chown app:app /app/stt/media

python <<'PY'
import os
import socket
import time

host = os.environ.get("POSTGRES_HOST", "postgres").strip() or "postgres"
port = int(os.environ.get("POSTGRES_PORT", "5432"))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        socket.create_connection((host, port), 2).close()
        break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f"PostgreSQL at {host}:{port} did not become reachable")
PY

if command -v runuser >/dev/null 2>&1; then
  exec runuser -u app -- python -m hub
fi
exec su --preserve-environment -s /bin/sh app -c 'exec python -m hub'
