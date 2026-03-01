#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="$ROOT/run-app.command"
NAME="Transcriptor de Video"
DESKTOP="$HOME/Desktop"
OUT="$DESKTOP/$NAME.command"

if [ ! -f "$TARGET" ]; then
  echo "No se encontro $TARGET"
  exit 1
fi

cp "$TARGET" "$OUT"
chmod +x "$OUT"

# Optional: remove quarantine if present
xattr -d com.apple.quarantine "$OUT" 2>/dev/null || true

echo "Acceso creado en: $OUT"
