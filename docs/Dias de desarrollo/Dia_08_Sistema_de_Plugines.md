# Día 08: Sistema de Plugins

Objetivo: habilitar extensibilidad mediante un sistema de plugins con hooks `on_start`, `on_message` y `on_stop`, integrados en `LucyAI` sin romper la arquitectura existente.

## Integración y Arquitectura
- Módulos nuevos:
  - `src/lucy/plugins/manager.py`: gestor de plugins, interfaz base y resultado (`PluginInterface`, `PluginResult`, `PluginManager`).
  - `src/lucy/plugins/__init__.py`: exporta las clases del sistema.
  - `src/lucy/plugins/builtins/echo_plugin.py`: plugin de ejemplo.
- Integración en `LucyAI` (`src/lucy/lucy_ai.py`):
  - Inicializa `PluginManager` en el constructor.
  - Ejecuta `plugin_manager.start(engine=self)` al inicio.
  - En `process_message`, antes del pipeline del modelo, llama `plugin_manager.handle_message(...)` y hace short-circuit si un plugin maneja el mensaje, actualizando el contexto.

## Configuración
- Se agregó sección `plugins` en `config/config.json`:
```json
"plugins": {
  "enabled": true,
  "dirs": ["src/lucy/plugins/builtins"]
}
```
- Compatibilidad con `features.plugins_enabled` si existe; el gestor activa plugins cuando cualquiera de las dos opciones esté habilitada.

## Interfaz del Plugin
- Clase base `PluginInterface` con métodos:
  - `on_start(engine, config)`
  - `on_message(message, context, engine) -> PluginResult`
  - `on_stop(engine)`
- `PluginResult` contiene:
  - `handled: bool` (si el plugin gestionó el mensaje)
  - `response: Optional[str]` (respuesta para short-circuit)
  - `meta: Dict[str, Any]` (información adicional)

## Descubrimiento y Carga
- Directorios configurables (`plugins.dirs`). Por defecto: `src/lucy/plugins/builtins`.
- Carga dinámica por archivo `*.py`, buscando clases que hereden de `PluginInterface`.
- Logging consistente usando `src/lucy/logging_system.get_logger`.

## Plugin de ejemplo: echo
- Responde a mensajes que comienzan con `!echo ` devolviendo `ECHO: <texto>`.
- Archivo: `src/lucy/plugins/builtins/echo_plugin.py`.

## Pruebas
- Se agregaron pruebas unitarias del gestor de plugins (descubrimiento y manejo de mensajes).
- Validan que:
  - Se puede cargar un plugin desde un directorio temporal.
  - `handle_message` retorna `PluginResult(handled=True)` con respuesta cuando aplica.

## Aceptación y Compatibilidad
- No se modifica el pipeline principal de `LucyAI` salvo la pre-evaluación de plugins; si ningún plugin maneja el mensaje, el flujo continúa igual.
- Configuración existente y pruebas previas se mantienen compatibles.
- Cumple con los criterios del plan de `docs/Semanas 2 y 3` para Día 8: modularidad, hooks, logging, configurabilidad y pruebas.

## Próximos pasos (Semana 2)
- Añadir plugins adicionales (reglas, utilidades, integraciones externas).
- Definir convenciones de metadata para enriquecer contexto.
- Documentar ejemplos y guía de desarrollo de plugins.