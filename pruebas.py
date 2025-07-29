import os
from core.training import DATA_DIR


print("Contenido de /core:")
print(os.listdir(DATA_DIR))
print("\nArchivos de idiomas:") 
print(f"Español: {os.path.exists(os.path.join(DATA_DIR, 'intents_es.json'))}")
print(f"Inglés: {os.path.exists(os.path.join(DATA_DIR, 'intents_en.json'))}")