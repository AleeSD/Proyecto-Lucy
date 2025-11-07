"""
Módulo de Memoria a Largo Plazo
===============================

Expone MemoryManager para inserción, consulta y purga de eventos conversacionales
con soporte de embeddings y búsqueda semántica.
"""

from .manager import MemoryManager

__all__ = ["MemoryManager"]