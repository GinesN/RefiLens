#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/runtime.sh
.venv/bin/ruff check services/api
.venv/bin/mypy --config-file services/api/pyproject.toml services/api/app
.venv/bin/pytest -c services/api/pyproject.toml services/api/tests
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web build
