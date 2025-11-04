#!/usr/bin/env bash
set -euo pipefail

echo "[Lucy] Configurando entorno (Linux/Mac)..."

if [ ! -d ".venv" ]; then
  echo "[Lucy] Creando entorno virtual .venv"
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "[Lucy] Instalando dependencias"
pip install --upgrade pip
pip install -r requirements.txt

pip install pytest pytest-cov

echo "[Lucy] Descargando datos NLTK (punkt, wordnet, omw-1.4)"
python3 - << 'PY'
import nltk
for pkg in ['punkt','wordnet','omw-1.4']:
    try:
        nltk.data.find(f'tokenizers/{pkg}' if pkg=='punkt' else f'corpora/{pkg}')
    except LookupError:
        nltk.download(pkg, quiet=True)
print('[Lucy] NLTK listo')
PY

echo "[Lucy] Entorno configurado exitosamente"