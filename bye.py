import os
import sys
from contextlib import contextmanager

@contextmanager
def suppress_tf_logs():
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    stderr = sys.stderr
    try:
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        sys.stderr = stderr

# Detect language utility
from langdetect import detect

def get_language(text: str) -> str:
    try:
        # Lista de idiomas soportados
        supported_langs = ['es', 'en']
        
        # Palabras clave para español como fallback
        spanish_keywords = ['hola', 'qué', 'cómo', 'por qué', 'gracias']
        
        # Primero intenta con langdetect
        lang = detect(text)
        
        # Si no es un idioma soportado, verifica palabras clave
        if lang not in supported_langs:
            if any(keyword in text.lower() for keyword in spanish_keywords):
                return 'es'
            return 'en'
        return lang
    except:
        return 'es'  # Default español si hay error