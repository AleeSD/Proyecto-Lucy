"""
Suite de Pruebas para Lucy AI
=============================

Módulo de testing que incluye pruebas unitarias y de integración
para todas las funcionalidades del sistema Lucy.
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

__version__ = "1.0.0"