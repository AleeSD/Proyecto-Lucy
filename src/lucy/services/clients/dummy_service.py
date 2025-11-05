"""
Servicio Dummy (builtin)
------------------------

Provee operaciones simples sin llamadas externas para pruebas:
- echo: retorna el texto recibido
- sum: retorna la suma de 'a' + 'b'
"""

from typing import Any, Dict

from ..manager import BaseServiceClient


class DummyServiceClient(BaseServiceClient):
    name = "dummy"
    version = "1.0.0"

    def execute(self, operation: str, params: Dict[str, Any]) -> Any:
        op = (operation or "").strip().lower()
        if op == "echo":
            text = str(params.get("text", ""))
            prefix = self.config.get("prefix", "")
            return f"{prefix}{text}" if prefix else text
        if op == "sum":
            a = float(params.get("a", 0))
            b = float(params.get("b", 0))
            return a + b
        raise ValueError(f"Operación no soportada: {operation}")