"""
Sistema de Plugins de Lucy AI
=============================

Define la interfaz base y exporta el gestor de plugins.
"""

from .manager import PluginManager, PluginInterface, PluginResult

__all__ = [
    "PluginManager",
    "PluginInterface",
    "PluginResult",
]