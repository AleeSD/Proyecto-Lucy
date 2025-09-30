# Día 05 - Sistema de Configuración Dinámico

## Qué se implementó
- Sistema de configuración dinámico en `core/config_manager.py`.
- Clase `ConfigWatcher` para monitorear cambios en archivos de configuración.
- Recarga automática de configuración en tiempo real.
- Sistema de observadores para notificar cambios a componentes.
- Detección y registro de cambios específicos en la configuración.
- Bloqueo de concurrencia para operaciones seguras en hilos.
- Integración con el sistema de logging.

## Cómo usarlo
- Inicializar: `config = ConfigManager(auto_reload=True)`
- Acceder a configuración: `api_key = config.get("api.key")`
- Registrar observador: `config.register_observer(mi_funcion_callback)`
- Forzar recarga: `config.reload_config()`
- Detectar cambios: Los cambios se detectan automáticamente y se registran en logs.

## Dónde configurar
- Archivo principal: `config/config.json`
- Modificar este archivo en tiempo real para que los cambios se apliquen automáticamente.
- No es necesario reiniciar la aplicación para aplicar cambios.

## Configuración rápida
- Habilitar/deshabilitar auto-recarga: `ConfigManager(auto_reload=True/False)`
- Intervalo de verificación: Modificable en la instancia de `ConfigWatcher`
- Observadores: Registrar/eliminar según necesidad con `register_observer`/`unregister_observer`

## Notas técnicas
- Utiliza hilos daemon para monitorear cambios sin bloquear la aplicación principal.
- Implementa bloqueo con `threading.RLock` para operaciones thread-safe.
- Detecta cambios específicos (añadidos, eliminados, modificados) en la configuración.
- Notifica a los componentes registrados solo cuando hay cambios reales.
- Maneja errores en observadores para evitar que un error en un componente afecte a otros.