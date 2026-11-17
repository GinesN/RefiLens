#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
echo ''
echo '  RefiLens — tu espacio de análisis de deuda'
echo ''
if [ ! -x .venv/bin/uvicorn ] || [ ! -d apps/web/node_modules ]; then ./scripts/setup.sh; fi
if .venv/bin/python - <<'PY'
import json, urllib.request
try:
    info = json.load(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=1))
    assert info.get('service') == 'refilens'
    urllib.request.urlopen('http://127.0.0.1:3000', timeout=1)
except Exception:
    raise SystemExit(1)
PY
then
  echo '  RefiLens ya está abierto. Abriendo la página…'
  open http://127.0.0.1:3000
  exit 0
fi
mkdir -p data
echo '  Iniciando RefiLens. El navegador se abrirá automáticamente.'
./scripts/dev.sh > data/refilens.log 2>&1 &
REFILENS_RUN_PID=$!
trap 'kill "$REFILENS_RUN_PID" 2>/dev/null || true' EXIT INT TERM
REFILENS_READY=0
for REFILENS_ATTEMPT in {1..60}; do
  if .venv/bin/python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:3000", timeout=2)' >/dev/null 2>&1; then
    open http://127.0.0.1:3000
    echo ''
    echo '  LISTO → http://localhost:3000'
    echo ''
    echo '  No necesitas escribir ningún comando.'
    echo '  Puedes minimizar esta ventana y usar la web.'
    echo '  Mantén esta ventana abierta mientras uses RefiLens.'
    echo '  Para apagarlo: pulsa Control + C.'
    echo ''
    echo '  Los mensajes técnicos se guardan en data/refilens.log.'
    REFILENS_READY=1
    break
  fi
  if ! kill -0 "$REFILENS_RUN_PID" 2>/dev/null; then
    echo '  No se ha podido iniciar. Consulta data/refilens.log.'
    echo '  Pulsa Intro para cerrar esta ventana.'
    read -r
    exit 1
  fi
  sleep 1
done
if [ "$REFILENS_READY" != 1 ]; then
  echo '  El inicio ha tardado demasiado. Consulta data/refilens.log.'
  echo '  Pulsa Intro para cerrar esta ventana.'
  read -r
  exit 1
fi
wait "$REFILENS_RUN_PID"
