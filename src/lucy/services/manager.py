"""
Gestor de Servicios Externos (Día 9)
===================================

Provee un ServiceManager para integrar APIs externas de forma modular.
Cada servicio implementa BaseServiceClient con método `execute(operation, params)`.
"""

import logging
from typing import Any, Dict, Optional
from pathlib import Path

from ..config_manager import ConfigManager
from ..logging_system import get_logger


class BaseServiceClient:
    """Interfaz base para clientes de servicios externos"""

    name: str = "service"
    version: str = "0.1.0"

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}

    def execute(self, operation: str, params: Dict[str, Any]) -> Any:
        raise NotImplementedError


class ServiceManager:
    """Gestor central de servicios externos"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = config_manager.get_all()
        self.logger = get_logger("lucy.services")
        self._clients: Dict[str, BaseServiceClient] = {}
        self._load_clients()

    def _is_enabled(self) -> bool:
        return bool(self.config.get("external_services", {}).get("enabled", False))

    def _load_clients(self):
        """Carga clientes según configuración; incluye dummy builtin por defecto"""
        if not self._is_enabled():
            self.logger.info("[Services] Integración desactivada")
            return

        services_cfg = self.config.get("external_services", {}).get("services", {})

        # Dummy builtin siempre disponible si está habilitado
        try:
            from .clients.dummy_service import DummyServiceClient
            self._clients["dummy"] = DummyServiceClient(services_cfg.get("dummy", {}))
        except Exception as e:
            self.logger.error(f"[Services] Error cargando dummy: {e}")

        # Futuro: cargar otros clientes según config (http, weather, etc.)

        self.logger.info(f"[Services] Clientes activos: {list(self._clients.keys())}")

    def execute(self, service: str, operation: str, params: Dict[str, Any]) -> Optional[Any]:
        """Ejecuta una operación en el servicio indicado"""
        if not self._is_enabled():
            self.logger.warning("[Services] Llamada ignorada: servicios desactivados")
            return None
        client = self._clients.get(service)
        if not client:
            self.logger.warning(f"[Services] Servicio no encontrado: {service}")
            return None
        try:
            return client.execute(operation, params or {})
        except Exception as e:
            self.logger.error(f"[Services] Error ejecutando {service}.{operation}: {e}")
            return None