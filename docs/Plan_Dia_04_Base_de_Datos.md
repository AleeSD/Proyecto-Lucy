# Día 04 - Base de Datos para Conversaciones y Contexto

## Qué se implementó
- Sistema completo de base de datos SQLite en `src/lucy/database.py`.
- Clase `ConversationDB` con métodos para gestionar conversaciones y contexto.
- Tablas: `conversations`, `sessions`, `context`, `learning_data` y `metrics`.
- Funciones para crear sesiones, almacenar conversaciones y gestionar contexto.
- Sistema de expiración de contexto con tiempo configurable.
- Historial de conversaciones con límite personalizable.
- Integración con el sistema de logging.

## Cómo usarlo
- Inicializar: `db = ConversationDB("data/lucy.db")`
- Crear sesión: `session_id = db.create_session(user_name="Usuario")`
- Guardar conversación: `db.save_conversation(session_id, "Hola", "¡Hola! ¿En qué puedo ayudarte?")`
- Establecer contexto: `db.set_context(session_id, "última_consulta", "clima", expiry_minutes=30)`
- Obtener contexto: `última_consulta = db.get_context(session_id, "última_consulta")`
- Obtener historial: `historial = db.get_conversation_history(session_id, limit=5)`

## Dónde se almacenan los datos
- Base de datos principal: `data/lucy.db`
- Tablas principales:
  - `conversations`: Almacena todas las interacciones usuario-bot
  - `sessions`: Información de sesiones de usuario
  - `context`: Datos de contexto con expiración configurable
  - `learning_data`: Patrones aprendidos para futuras respuestas
  - `metrics`: Métricas de rendimiento y uso

## Configuración rápida
- La base de datos se crea automáticamente si no existe.
- El contexto puede configurarse con tiempo de expiración en minutos.
- El historial de conversaciones puede limitarse según necesidad.

## Notas técnicas
- Utiliza SQLite para portabilidad y simplicidad.
- Implementa índices para optimizar consultas frecuentes.
- El contexto se almacena en formato JSON para flexibilidad.
- Sistema de limpieza automática de contextos expirados.
- Integración con el sistema de logging para seguimiento de operaciones.