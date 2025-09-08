# Día 02 - Sistema de Logging y Monitoreo

## Qué se implementó
- Gestor central de logging en `core/logging_system.py` (JSON, rotación, colores, Loguru).
- Integración en `lucy.py`: uso de `get_logger`, `log_conversation`, `log_performance`, `log_error`.
- Conversaciones JSON: `logs/conversations/conversations.json`.
- Métricas de rendimiento: `logs/performance/performance.log`.
- Errores con alertas: `logs/errors/errors.log`.
- Configuración en `config/logging.yaml` (formatos, niveles, handlers).
- Nuevas dependencias en `requirements.txt` para logging y monitoreo.

## Cómo usarlo
- Ejecuta: `python lucy.py`.
- Cada interacción registra conversación, métrica `response_time` y errores si ocurren.

## Dónde ver los logs
- General: `logs/lucy.log`.
- Errores: `logs/lucy_errors.log` y `logs/errors/errors.log`.
- Conversaciones: `logs/conversations/conversations.json`.
- Rendimiento: `logs/performance/performance.log`.

## Configuración rápida
- Edita `config/logging.yaml` para niveles, rotación y formateadores.
- Claves útiles: `handlers.console.level`, `handlers.file_handler.maxBytes`, `loggers.core.lucy_ai.level`.

## Notas técnicas
- El sistema se inicializa al importar `core.logging_system`.
- Funciones disponibles: `get_logger`, `log_conversation`, `log_performance`, `log_error`.
- Si falla el logger avanzado, existe fallback al logger básico.
