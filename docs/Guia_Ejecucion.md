# Guía de Ejecución de Lucy AI

Esta guía explica cómo ejecutar Lucy AI, configurar parámetros y entender rutas de logs y base de datos.

## Arranque básico
```bash
# Con entorno activado
python lucy.py

# O usando los scripts
run_lucy.bat          # Windows
bash run_lucy.sh      # Linux/Mac
```

## Configuración
- Archivo: `config/config.json`
- Parámetros comunes:
  - `model.default_language`: idioma por defecto (`es`/`en`)
  - `model.confidence_threshold`: umbral de confianza (0.0–1.0)
  - `paths.intents_dir`, `paths.models_dir`, `paths.logs_dir`

Los cambios pueden aplicarse en runtime si `ConfigWatcher` está habilitado.

## Datos y modelos
- Intents: `data/intents/intents_es.json`, `data/intents/intents_en.json`
- Modelos: `data/models/lucy_model.h5`, `words.pkl`, `classes.pkl`
- Si faltan modelos, Lucy funciona en modo básico (heurísticas y intents).

## Logs y auditoría
- Logs generales: `logs/lucy.log`
- Conversaciones: `logs/conversations/conversations.json`
- Métricas: `logs/performance/performance.log`
- Errores: `logs/errors/errors.log`

## Base de datos
- SQLite en: `data/conversations.db` (según config)
- APIs clave (ver `src/lucy/database.py`):
  - `save_conversation(session_id, user_input, bot_response, ...)`
  - `get_conversation_history(session_id, limit=50)`
  - `get_metrics_summary(hours=24)`
  - `cleanup_old_data(days_to_keep=30)`

## Operación y comandos
En el chat interactivo:
- `/help`, `/config`, `/stats`, `/clear`, `/exit`

## Troubleshooting rápido
- NLTK faltante: se descarga automáticamente al iniciar.
- TF/Keras falla: Lucy degrada a modo básico sin ML.
- Codificación en Windows: scripts y `PYTHONUTF8=1` están configurados.