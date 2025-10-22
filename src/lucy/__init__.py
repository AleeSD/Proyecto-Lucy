"""
Módulo Core de Lucy AI
=====================

Este módulo contiene la funcionalidad principal del asistente Lucy:
- Procesamiento de lenguaje natural
- Sistema de entrenamiento
- Gestión de configuración
- Utilidades generales

Author: AleeSD
Version: 1.0.0
"""

from .lucy_ai import LucyAI
from .config_manager import ConfigManager, get_config_manager
from .utils import get_language, suppress_tf_logs
from .database import ConversationDB

__version__ = "1.0.0"
__author__ = "AleeSD"

# Configurar logging al importar el módulo
import logging
import os

def setup_logging():
    """Configuración inicial de logging"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'lucy.log')),
            logging.StreamHandler()
        ]
    )

# Inicializar logging
setup_logging()

# Exportar clases principales
__all__ = [
    'LucyAI',
    'ConfigManager',
    'get_config_manager',
    'ConversationDB',
    'get_language',
    'suppress_tf_logs'
]