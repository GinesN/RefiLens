#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
REFILENS_WEB_COMMAND=start exec ./scripts/dev.sh
