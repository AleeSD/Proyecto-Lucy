#!/usr/bin/env bash
set -euo pipefail

echo "[Lucy] Preparando entorno..."
# Activar entorno virtual si existe
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

export PYTHONUTF8=1
export PYTHONPATH="$(pwd)"

echo "[Lucy] Iniciando Lucy AI..."
python3 lucy.py "$@"

echo "[Lucy] Finalizado."
