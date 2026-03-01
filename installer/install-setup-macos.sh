#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG="$(dirname "$0")/install-setup-macos.log"

log() {
  echo "$1"
  printf "%s %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "$LOG"
}

log "=== Instalacion desde cero (macOS) ==="

if ! command -v brew >/dev/null 2>&1; then
  log "Homebrew no esta instalado. Instalalo desde https://brew.sh y vuelve a ejecutar."
  exit 1
fi

log "Instalando Python..."
brew install python@3.11 || brew upgrade python@3.11

log "Instalando FFmpeg..."
brew install ffmpeg || brew upgrade ffmpeg

log "Instalando ngrok..."
brew install ngrok/ngrok/ngrok || brew upgrade ngrok/ngrok/ngrok

PYBIN="$(brew --prefix python@3.11)/bin/python3.11"
if [ ! -x "$PYBIN" ]; then
  PYBIN="python3"
fi

log "Creando venv (si no existe)..."
if [ ! -x "$ROOT/venv/bin/python" ]; then
  "$PYBIN" -m venv "$ROOT/venv"
fi

log "Actualizando pip..."
./venv/bin/python -m pip install --upgrade pip

log "Instalando dependencias del proyecto..."
./venv/bin/python -m pip install -r "$ROOT/requirements.txt"

log "Reinstalando Pillow compatible (moviepy requiere <12)..."
./venv/bin/python -m pip install --upgrade --force-reinstall --no-cache-dir "pillow<12"

log "Listo."
