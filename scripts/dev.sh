#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/runtime.sh
.venv/bin/python - <<'PY'
import socket
for port in (8000, 3000):
    with socket.socket() as connection:
        if connection.connect_ex(('127.0.0.1', port)) == 0:
            raise SystemExit(f'Port {port} is already in use. Close the existing local server before starting RefiLens.')
PY
cleanup() {
  kill "${REFILENS_API_PID:-}" "${REFILENS_WEB_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
PYTHONPATH=services/api .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir services/api/app &
REFILENS_API_PID=$!
pnpm --dir apps/web "${REFILENS_WEB_COMMAND:-dev}" &
REFILENS_WEB_PID=$!
echo 'RefiLens: http://localhost:3000 • API: http://127.0.0.1:8000/docs'
while kill -0 "$REFILENS_API_PID" 2>/dev/null && kill -0 "$REFILENS_WEB_PID" 2>/dev/null; do sleep 1; done
echo 'A RefiLens service stopped. See the server output above.' >&2
exit 1
