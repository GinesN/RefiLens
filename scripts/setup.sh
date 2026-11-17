#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/runtime.sh
"$REFILENS_PYTHON" -m venv .venv
.venv/bin/python -m pip install uv
UV_PROJECT_ENVIRONMENT="$PWD/.venv" .venv/bin/uv sync --project services/api --python "$REFILENS_PYTHON" --frozen
pnpm --dir apps/web install --frozen-lockfile
if [ ! -f .env ]; then cp .env.example .env; chmod 600 .env; fi
.venv/bin/alembic -c services/api/alembic.ini upgrade head
for refilens_ticker in NUE STLD RS LECO ITW; do
  refilens_snapshot=$(printf '%s' "$refilens_ticker" | tr '[:upper:]' '[:lower:]')
  PYTHONPATH=services/api .venv/bin/python -m app.ingestion.import_company --ticker "$refilens_ticker" --snapshot "fixtures/$refilens_snapshot-2025.json"
done
echo 'Ready. Run ./scripts/dev.sh and open http://localhost:3000'
