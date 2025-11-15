"""
Gestor de Plugins para Lucy AI (Día 8)
=====================================

Provee un sistema extensible con hooks:
- on_start(engine, config)
- on_message(message, context, engine) -> PluginResult
- on_stop(engine)

Los plugins se cargan dinámicamente desde directorios configurables.
Cada plugin debe exponer una clase que implemente PluginInterface.
"""

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config_manager import ConfigManager
from ..logging_system import get_logger


@dataclass
class PluginResult:
    """Resultado de ejecución de un plugin"""
    handled: bool = False
    response: Optional[str] = None
    meta: Dict[str, Any] = None


class PluginInterface:
    """Interfaz base para plugins de Lucy"""

    name: str = "plugin"
    version: str = "0.1.0"

    def on_start(self, engine: Any, config: Dict[str, Any]):
        pass

    def on_message(self, message: str, context: List[Dict[str, Any]], engine: Any) -> PluginResult:
        return PluginResult(handled=False)

    def on_stop(self, engine: Any):
        pass


class PluginManager:
    """Gestor central del sistema de plugins"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = config_manager.get_all()
        self.logger = get_logger("lucy.plugins")
        self._plugins: List[PluginInterface] = []
        self._engine = None

    def _is_enabled(self) -> bool:
        # Activación por dos esquemas compatibles: features.plugins_enabled o plugins.enabled
        if self.config_manager.is_feature_enabled("plugins_enabled"):
            return True
        return bool(self.config.get("plugins", {}).get("enabled", False))

    def _get_plugin_dirs(self) -> List[Path]:
        dirs = self.config.get("plugins", {}).get("dirs")
        if not dirs:
            # Directorio por defecto: plugins builtin
            default = Path(__file__).parent / "builtins"
            return [default]
        paths = []
        for d in dirs:
            p = Path(d)
            if not p.is_absolute():
                # Resolver relativo al proyecto
                project_root = Path(__file__).parents[3]
                p = project_root / d
            paths.append(p)
        return paths

    def discover_plugins(self) -> List[PluginInterface]:
        """Descubre y carga plugins desde los directorios configurados"""
        discovered: List[PluginInterface] = []
        for dir_path in self._get_plugin_dirs():
            try:
                if not dir_path.exists():
                    self.logger.warning(f"[Plugins] Directorio no encontrado: {dir_path}")
                    continue
                for file in dir_path.glob("*.py"):
                    plugin = self._load_plugin_from_file(file)
                    if plugin:
                        discovered.append(plugin)
            except Exception as e:
                self.logger.error(f"[Plugins] Error descubriendo plugins en {dir_path}: {e}", exc_info=True)
        return discovered

    def _load_plugin_from_file(self, file_path: Path) -> Optional[PluginInterface]:
        try:
            spec = importlib.util.spec_from_file_location(file_path.stem, str(file_path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore
                # Buscar clase que implemente PluginInterface
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    try:
                        if isinstance(attr, type) and issubclass(attr, PluginInterface) and attr is not PluginInterface:
                            instance: PluginInterface = attr()
                            self.logger.debug(f"[Plugins] Cargado plugin: {instance.name} v{instance.version}")
                            return instance
                    except Exception:
                        continue
            self.logger.warning(f"[Plugins] No se encontró clase de plugin en: {file_path}")
        except Exception as e:
            self.logger.error(f"[Plugins] Error cargando plugin {file_path}: {e}", exc_info=True)
        return None

    def start(self, engine: Any = None):
        """Inicializa el sistema de plugins y ejecuta on_start"""
        if not self._is_enabled():
            self.logger.info("[Plugins] Sistema desactivado")
            return
        self._engine = engine
        self._plugins = self.discover_plugins()
        for p in self._plugins:
            try:
                p.on_start(self._engine, self.config.get("plugins", {}))
            except Exception as e:
                self.logger.error(f"[Plugins] Error en on_start de {getattr(p, 'name', p)}: {e}")

        self.logger.info(f"[Plugins] Inicializados: {len(self._plugins)}")

    def handle_message(self, message: str, context: List[Dict[str, Any]]) -> PluginResult:
        """Ejecuta los plugins sobre un mensaje; permite short-circuit"""
        if not self._is_enabled() or not self._plugins:
            return PluginResult(handled=False)
        for p in self._plugins:
            try:
                result = p.on_message(message, context, self._engine)
                if result and result.handled:
                    self.logger.debug(f"[Plugins] Mensaje manejado por {getattr(p, 'name', p)}")
                    return result
            except Exception as e:
                self.logger.error(f"[Plugins] Error en on_message de {getattr(p, 'name', p)}: {e}")
                continue
        return PluginResult(handled=False)

    def stop(self):
        """Finaliza el sistema de plugins, ejecutando on_stop"""
        if not self._is_enabled() or not self._plugins:
            return
        for p in self._plugins:
            try:
                p.on_stop(self._engine)
            except Exception as e:
                self.logger.error(f"[Plugins] Error en on_stop de {getattr(p, 'name', p)}: {e}")
        self.logger.info("[Plugins] Sistema detenido")