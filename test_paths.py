# test_paths.py - Versión definitiva
import os

# Ruta absoluta del directorio del proyecto
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "data")

print(f"Directorio del proyecto: {PROJECT_DIR}")
print(f"¿Existe data/intents.json? {os.path.exists(os.path.join(DATA_DIR, 'intents.json'))}")
print(f"Contenido de /data: {os.listdir(DATA_DIR)}")