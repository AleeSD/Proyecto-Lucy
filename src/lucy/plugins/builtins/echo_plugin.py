"""
Plugin de ejemplo: Echo
----------------------

Responde a mensajes que comiencen con el prefijo "!echo ".
"""

from typing import Any, Dict, List

from lucy.plugins.manager import PluginInterface, PluginResult


class EchoPlugin(PluginInterface):
    name = "echo"
    version = "1.0.0"

    def on_start(self, engine: Any, config: Dict[str, Any]):
        # No requiere inicialización compleja
        pass

    def on_message(self, message: str, context: List[Dict[str, Any]], engine: Any) -> PluginResult:
        if message.strip().lower().startswith("!echo "):
            return PluginResult(handled=True, response=f"ECHO: {message[6:]}", meta={"plugin": self.name})
        return PluginResult(handled=False)

    def on_stop(self, engine: Any):
        # Limpieza si aplica
        pass