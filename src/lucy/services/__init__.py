"""
Servicios Externos de Lucy AI
=============================

Exporta el gestor y la interfaz base de clientes de servicios.
"""

from .manager import ServiceManager, BaseServiceClient

__all__ = ["ServiceManager", "BaseServiceClient"]