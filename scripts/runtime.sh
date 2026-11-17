#!/usr/bin/env bash
# Bundled Codex runtimes are a fallback; ordinary installed runtimes take precedence.
REFILENS_BUNDLE="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies"
if ! command -v node >/dev/null 2>&1 && [ -x "$REFILENS_BUNDLE/node/bin/node" ]; then
  export PATH="$REFILENS_BUNDLE/node/bin:$PATH"
fi
if ! command -v pnpm >/dev/null 2>&1 && [ -x "$REFILENS_BUNDLE/bin/fallback/pnpm" ]; then
  export PATH="$REFILENS_BUNDLE/bin/fallback:$PATH"
fi
REFILENS_PYTHON="${REFILENS_PYTHON:-python3}"
if ! "$REFILENS_PYTHON" -c 'import sys; assert sys.version_info >= (3,12)' 2>/dev/null; then
  if [ -x "$REFILENS_BUNDLE/python/bin/python3" ]; then
    REFILENS_PYTHON="$REFILENS_BUNDLE/python/bin/python3"
  else
    echo 'Install Python 3.12+ or set REFILENS_PYTHON to its executable.' >&2
    exit 1
  fi
fi
