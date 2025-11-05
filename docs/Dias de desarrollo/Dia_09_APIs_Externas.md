# Día 09 – Integración de APIs Externas

Este día incorpora un gestor de servicios para integrar APIs externas de forma modular y segura, con un servicio `dummy` builtin para pruebas sin dependencias de red y un comando de acceso directo desde LucyAI.

## Objetivos
- Añadir `ServiceManager` para orquestar servicios externos.
- Definir interfaz `BaseServiceClient` para clientes.
- Incluir servicio `dummy` con operaciones `echo` y `sum`.
- Integrar el comando `!api` en `LucyAI.process_message`.
- Configurar sección `external_services` en `config/config.json`.
- Crear pruebas unitarias del gestor.

## Arquitectura
- `src/lucy/services/manager.py`: gestor central, carga clientes y ejecuta operaciones.
- `src/lucy/services/clients/dummy_service.py`: servicio builtin sin llamadas externas.
- `src/lucy/lucy_ai.py`: inicializa `ServiceManager` y maneja el comando `!api`.

## Configuración
Se añadió la sección `external_services` en `config/config.json`:

```json
"external_services": {
  "enabled": true,
  "services": {
    "dummy": { "prefix": "" }
  }
}
```

## Interfaz de Servicio
```python
class BaseServiceClient:
    def execute(self, operation: str, params: Dict[str, Any]) -> Any: ...
```

## Comando en LucyAI
Formato: `!api <servicio> <operacion> [k=v]...`

Ejemplos:
- `!api dummy echo text=hola` → "hola"
- `!api dummy sum a=2 b=3` → "5"

La respuesta se guarda en el contexto conversacional.

## Pruebas
- `tests/test_services.py` valida carga y ejecución del servicio `dummy` y comportamiento desactivado.

## Criterios de Aceptación
- ServiceManager instanciado y operativo con `external_services.enabled=true`.
- LucyAI ejecuta `!api` y devuelve resultados.
- Pruebas unitarias pasan sin romper el resto del suite.

## Próximos pasos
- Añadir clientes HTTP reales con mocking en pruebas.
- Soporte de autenticación y reintentos.
- Métricas y logging específico por servicio.