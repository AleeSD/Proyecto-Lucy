# Guía de Instalación de Lucy AI

Esta guía te ayuda a preparar el entorno de Lucy AI en Windows, Linux o macOS.

## Requisitos
- Python 3.8 o superior
- Git
- Conexión a internet (para descargar datos NLTK)

## Pasos

### 1) Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd Proyecto-Lucy
```

### 2) Crear entorno virtual
```bash
# Windows (PowerShell)
python -m venv .venv
./.venv/Scripts/Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Descargar datos NLTK (opcional)
Lucy descargará automáticamente `punkt`, `wordnet` y `omw-1.4` al iniciar. Si prefieres manual:
```python
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
```

### 5) Preparación automática
Puedes usar los scripts para automatizar los pasos anteriores:
```bash
# Windows
scripts/setup_env.ps1

# Linux/Mac
bash scripts/setup_env.sh
```

## Verificación
Ejecuta los tests:
```bash
pytest -q --cov=src/lucy --cov-report=term-missing
```

Si todo está correcto, puedes iniciar Lucy:
```bash
python lucy.py
```