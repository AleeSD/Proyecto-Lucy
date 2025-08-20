"""
Utilidades Generales para Lucy AI
=================================

Funciones de utilidad para el procesamiento de lenguaje, 
manejo de archivos y configuración del entorno.
"""

import os
import sys
import logging
import time
import langdetect
from contextlib import contextmanager
from functools import wraps
from typing import List, Dict, Any, Optional

# Configurar TensorFlow para suprimir mensajes
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

logger = logging.getLogger(__name__)

@contextmanager
def suppress_tf_logs():
    """
    Context manager para suprimir completamente los logs de TensorFlow
    """
    # Guardar stderr original
    original_stderr = sys.stderr
    
    try:
        # Redirigir stderr a devnull
        sys.stderr = open(os.devnull, 'w')
        yield
    finally:
        # Restaurar stderr original
        if hasattr(sys.stderr, 'close'):
            sys.stderr.close()
        sys.stderr = original_stderr

def get_language(text: str) -> str:
    """
    Detecta el idioma de un texto dado
    
    Args:
        text: Texto a analizar
        
    Returns:
        Código de idioma ('es' o 'en')
    """
    try:
        from langdetect import detect
        
        # Lista de idiomas soportados
        supported_langs = ['es', 'en']
        
        # Palabras clave para detección manual como fallback
        spanish_keywords = {
            'hola', 'qué', 'cómo', 'por', 'para', 'con', 'una', 'del', 'las',
            'gracias', 'adiós', 'buenos', 'buenas', 'días', 'tardes', 'noches',
            'soy', 'estoy', 'tengo', 'quiero', 'necesito', 'puedes', 'ayuda'
        }
        
        english_keywords = {
            'hello', 'what', 'how', 'when', 'where', 'why', 'the', 'and', 'for',
            'thank', 'thanks', 'goodbye', 'good', 'morning', 'afternoon', 'evening',
            'am', 'are', 'have', 'want', 'need', 'can', 'help', 'please'
        }
        
        # Limpiar texto para análisis
        clean_text = text.lower().strip()
        
        # Si el texto es muy corto, usar palabras clave
        if len(clean_text.split()) <= 2:
            words = set(clean_text.split())
            
            spanish_matches = len(words.intersection(spanish_keywords))
            english_matches = len(words.intersection(english_keywords))
            
            if spanish_matches > english_matches:
                return 'es'
            elif english_matches > spanish_matches:
                return 'en'
        
        # Usar langdetect para textos más largos
        detected_lang = detect(clean_text)
        
        # Verificar si el idioma detectado está soportado
        if detected_lang in supported_langs:
            return detected_lang
        
        # Fallback a análisis de palabras clave
        words = set(clean_text.split())
        spanish_score = len(words.intersection(spanish_keywords))
        english_score = len(words.intersection(english_keywords))
        
        return 'es' if spanish_score >= english_score else 'en'
        
    except Exception as e:
        logger.warning(f"Error en detección de idioma: {e}")
        return 'es'  # Default a español

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitiza la entrada del usuario
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        Texto sanitizado
    """
    if not isinstance(text, str):
        return ""
    
    # Limpiar y truncar
    sanitized = text.strip()[:max_length]
    
    # Remover caracteres de control peligrosos
    control_chars = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f'
    for char in control_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized

def validate_file_path(file_path: str, allowed_extensions: List[str] = None) -> bool:
    """
    Valida que una ruta de archivo sea segura
    
    Args:
        file_path: Ruta del archivo
        allowed_extensions: Extensiones permitidas
        
    Returns:
        True si la ruta es válida y segura
    """
    try:
        path = os.path.normpath(file_path)
        
        # Verificar que no hay path traversal
        if '..' in path or path.startswith('/'):
            return False
        
        # Verificar extensión si se especifica
        if allowed_extensions:
            _, ext = os.path.splitext(path)
            if ext.lower() not in allowed_extensions:
                return False
        
        return True
        
    except Exception:
        return False

def measure_execution_time(func):
    """
    Decorador para medir tiempo de ejecución de funciones
    
    Args:
        func: Función a decorar
        
    Returns:
        Función decorada que loggea el tiempo de ejecución
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        logger.debug(f"{func.__name__} ejecutado en {execution_time:.4f} segundos")
        return result
    
    return wrapper

def load_json_file(file_path: str, encoding: str = 'utf-8') -> Optional[Dict[str, Any]]:
    """
    Carga un archivo JSON de forma segura
    
    Args:
        file_path: Ruta al archivo JSON
        encoding: Codificación del archivo
        
    Returns:
        Diccionario con el contenido o None si hay error
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Archivo no encontrado: {file_path}")
            return None
            
        with open(file_path, 'r', encoding=encoding) as f:
            return json.load(f)
            
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON en {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error cargando archivo {file_path}: {e}")
        return None

def save_json_file(data: Dict[str, Any], file_path: str, encoding: str = 'utf-8') -> bool:
    """
    Guarda datos en un archivo JSON
    
    Args:
        data: Datos a guardar
        file_path: Ruta del archivo
        encoding: Codificación del archivo
        
    Returns:
        True si se guardó correctamente
    """
    try:
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Archivo guardado: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error guardando archivo {file_path}: {e}")
        return False

def get_system_info() -> Dict[str, str]:
    """
    Obtiene información básica del sistema
    
    Returns:
        Diccionario con información del sistema
    """
    import platform
    
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'architecture': platform.architecture()[0],
        'python_version': platform.python_version(),
        'hostname': platform.node()
    }

def format_file_size(size_bytes: int) -> str:
    """
    Formatea el tamaño de archivo en formato legible
    
    Args:
        size_bytes: Tamaño en bytes
        
    Returns:
        Tamaño formateado (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def create_session_id() -> str:
    """
    Genera un ID único para sesión
    
    Returns:
        ID de sesión único
    """
    import uuid
    import time
    
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"lucy_{timestamp}_{unique_id}"

class PerformanceMonitor:
    """Monitor simple de rendimiento"""
    
    def __init__(self):
        self.metrics = {}
        
    def start_timer(self, operation: str):
        """Inicia un timer para una operación"""
        self.metrics[operation] = {'start_time': time.time()}
    
    def end_timer(self, operation: str) -> float:
        """
        Termina un timer y retorna el tiempo transcurrido
        
        Args:
            operation: Nombre de la operación
            
        Returns:
            Tiempo transcurrido en segundos
        """
        if operation in self.metrics:
            elapsed = time.time() - self.metrics[operation]['start_time']
            self.metrics[operation]['duration'] = elapsed
            logger.debug(f"Operación '{operation}' completada en {elapsed:.4f}s")
            return elapsed
        return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna todas las métricas recolectadas"""
        return self.metrics.copy()
    
    def reset(self):
        """Reinicia todas las métricas"""
        self.metrics.clear()

# Instancia global del monitor de rendimiento
performance_monitor = PerformanceMonitor()

def log_error_with_context(error: Exception, context: Dict[str, Any] = None):
    """
    Loggea un error con contexto adicional
    
    Args:
        error: Excepción a loggear
        context: Contexto adicional para debug
    """
    error_msg = f"Error: {type(error).__name__}: {str(error)}"
    
    if context:
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg += f" | Contexto: {context_str}"
    
    logger.error(error_msg, exc_info=True)

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorador para reintentar operaciones que fallan
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Delay entre intentos en segundos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Intento {attempt + 1} falló para {func.__name__}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"Todos los intentos fallaron para {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

# Importar json después de definir las otras funciones
import json