"""
Compatibilidad temporal de paquete core
=====================================

Este paquete actúa como capa de compatibilidad y reexporta
las interfaces desde el paquete principal `lucy` ubicado en `src/`.

Se recomienda migrar a imports desde `lucy.*`.
"""

# Asegurar que el paquete `lucy` bajo `src/` esté en sys.path
import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parents[1] / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Reexportar todo desde el paquete lucy
from lucy import *