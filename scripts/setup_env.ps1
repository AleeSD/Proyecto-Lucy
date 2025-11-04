#requires -Version 5.1
param()

Write-Host "[Lucy] Configurando entorno (Windows)..." -ForegroundColor Cyan

# Crear venv si no existe
if (-Not (Test-Path ".\.venv")) {
  Write-Host "[Lucy] Creando entorno virtual .venv" -ForegroundColor Yellow
  python -m venv .venv
}

# Activar venv
Write-Host "[Lucy] Activando entorno virtual" -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Actualizar pip y dependencias
Write-Host "[Lucy] Instalando dependencias" -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Pytest y cobertura (opcional)
python -m pip install pytest pytest-cov

# Descargar NLTK (silencioso)
Write-Host "[Lucy] Descargando datos NLTK (punkt, wordnet, omw-1.4)" -ForegroundColor Yellow
python - << 'PY'
import nltk
for pkg in ['punkt','wordnet','omw-1.4']:
    try:
        nltk.data.find(f'tokenizers/{pkg}' if pkg=='punkt' else f'corpora/{pkg}')
    except LookupError:
        nltk.download(pkg, quiet=True)
print('[Lucy] NLTK listo')
PY

Write-Host "[Lucy] Entorno configurado exitosamente" -ForegroundColor Green