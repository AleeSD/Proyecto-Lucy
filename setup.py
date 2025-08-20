"""
Script de instalación y configuración para Proyecto Lucy
========================================================

Maneja la instalación automática, configuración inicial y verificación del sistema.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import shutil

def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - Compatible")
    return True

def install_requirements():
    """Instala las dependencias requeridas"""
    print("📦 Instalando dependencias...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias: {e}")
        return False

def download_nltk_data():
    """Descarga los datos necesarios de NLTK"""
    print("🔤 Descargando recursos de NLTK...")
    
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
        print("✅ Recursos de NLTK descargados")
        return True
    except Exception as e:
        print(f"❌ Error descargando recursos NLTK: {e}")
        return False

def create_directory_structure():
    """Crea la estructura de directorios necesaria"""
    print("📁 Creando estructura de directorios...")
    
    directories = [
        "config",
        "data",
        "data/intents", 
        "data/models",
        "logs",
        "tests",
        "docs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   📂 {directory}/")
    
    print("✅ Estructura de directorios creada")

def move_existing_files():
    """Reorganiza archivos existentes a la nueva estructura"""
    print("🔄 Reorganizando archivos existentes...")
    
    # Mapeo de archivos a mover
    moves = [
        ("core/intents_es.json", "data/intents/intents_es.json"),
        ("core/intents_en.json", "data/intents/intents_en.json"),
        ("core/intents.json", "data/intents/intents_es.json")  # Fallback
    ]
    
    # Archivos del modelo (si existen en raíz)
    model_files = ["words.pkl", "classes.pkl", "lucy_model.h5"]
    for file in model_files:
        if Path(file).exists():
            moves.append((file, f"data/models/{file}"))
    
    for source, destination in moves:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if source_path.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))
            print(f"   📄 {source} → {destination}")
    
    print("✅ Archivos reorganizados")

def create_default_config():
    """Crea archivo de configuración por defecto si no existe"""
    config_path = Path("config/config.json")
    
    if config_path.exists():
        print("ℹ️  Archivo de configuración ya existe")
        return
    
    print("⚙️  Creando configuración por defecto...")
    
    default_config = {
        "app": {
            "name": "Lucy AI",
            "version": "1.0.0",
            "author": "AleeSD"
        },
        "model": {
            "default_language": "es",
            "supported_languages": ["es", "en"],
            "confidence_threshold": 0.25,
            "training_epochs": 200,
            "batch_size": 5
        },
        "paths": {
            "data_dir": "data",
            "models_dir": "data/models",
            "intents_dir": "data/intents",
            "logs_dir": "logs"
        },
        "database": {
            "path": "data/conversations.db",
            "backup_enabled": true
        },
        "logging": {
            "level": "INFO",
            "file_enabled": true,
            "console_enabled": true
        },
        "features": {
            "voice_recognition": false,
            "web_search": false,
            "plugins_enabled": false
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print("✅ Configuración por defecto creada")

def verify_installation():
    """Verifica que la instalación sea correcta"""
    print("🔍 Verificando instalación...")
    
    # Verificar archivos críticos
    critical_files = [
        "lucy.py",
        "core/lucy_ai.py",
        "core/utils.py", 
        "config/config.json",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in critical_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("❌ Archivos críticos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    # Verificar directorios
    required_dirs = ["data", "data/intents", "data/models", "logs", "config"]
    missing_dirs = []
    for directory in required_dirs:
        if not Path(directory).exists():
            missing_dirs.append(directory)
    
    if missing_dirs:
        print("❌ Directorios faltantes:")
        for directory in missing_dirs:
            print(f"   - {directory}/")
        return False
    
    # Verificar imports
    try:
        sys.path.insert(0, str(Path.cwd()))
        from core import ConfigManager
        print("✅ Imports de core funcionando")
    except ImportError as e:
        print(f"❌ Error en imports: {e}")
        return False
    
    print("✅ Instalación verificada correctamente")
    return True

def create_gitignore():
    """Crea archivo .gitignore si no existe"""
    gitignore_path = Path(".gitignore")
    
    if gitignore_path.exists():
        return
    
    gitignore_content = """# Lucy AI - GitIgnore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
pip-log.txt
pip-delete-this-directory.txt

# Virtual environments
lucy_env/
.env
.venv

# Lucy specific
logs/
*.log
temp/
data/conversations.db
data/models/*.h5
data/models/*.pkl
*.pkl

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Notebooks
.ipynb_checkpoints

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.coverage
.pytest_cache/
htmlcov/

# Documentation
docs/_build/
"""
    
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore creado")

def setup_initial_training():
    """Configura el entrenamiento inicial si es necesario"""
    model_path = Path("data/models/lucy_model.h5")
    
    if model_path.exists():
        print("ℹ️  Modelo ya existe, saltando entrenamiento inicial")
        return True
    
    print("🧠 Modelo no encontrado, iniciando entrenamiento inicial...")
    
    try:
        # Solo si el archivo de entrenamiento existe
        if Path("core/training.py").exists():
            subprocess.check_call([sys.executable, "core/training.py"])
            print("✅ Entrenamiento inicial completado")
            return True
        else:
            print("⚠️  Archivo de entrenamiento no encontrado")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en entrenamiento inicial: {e}")
        return False

def main():
    """Función principal de setup"""
    print("🤖 Configurando Proyecto Lucy...")
    print("=" * 50)
    
    # Verificaciones y configuración paso a paso
    steps = [
        ("Verificar Python", check_python_version),
        ("Crear estructura", create_directory_structure),
        ("Reorganizar archivos", move_existing_files),
        ("Crear configuración", create_default_config),
        ("Instalar dependencias", install_requirements),
        ("Descargar NLTK", download_nltk_data),
        ("Crear .gitignore", create_gitignore),
        ("Verificar instalación", verify_installation)
    ]
    
    failed_steps = []
    
    for step_name, step_function in steps:
        print(f"\n🔧 {step_name}...")
        try:
            if not step_function():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"❌ Error en {step_name}: {e}")
            failed_steps.append(step_name)
    
    # Resumen final
    print("\n" + "=" * 50)
    if failed_steps:
        print("⚠️  Instalación completada con errores:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n💡 Revisa los errores arriba y ejecuta setup.py nuevamente")
        return False
    else:
        print("🎉 ¡Instalación completada exitosamente!")
        print("\n🚀 Para ejecutar Lucy:")
        print("   python lucy.py")
        print("\n📖 Para más información:")
        print("   python lucy.py --help")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)