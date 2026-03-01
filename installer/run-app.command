#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "No se encontro el venv en $ROOT/venv. Ejecuta primero install-setup-macos.sh"
  exit 1
fi

cd "$ROOT"
"$PY" app.py
