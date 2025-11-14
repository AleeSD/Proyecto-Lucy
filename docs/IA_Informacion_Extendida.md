# Información técnica de Lucy AI

## Capacidades
- PLN multilingüe (es/en), normalización y lematización con NLTK
- Clasificación de intenciones con TensorFlow; fallback por reglas cuando la confianza es baja
- Plugins/Servicios extensibles con límites y aislamiento
- Memoria contextual y recuperación por embeddings
- Observabilidad: métricas de latencia, logging estructurado, trazas de conversación

## Arquitectura
- Núcleo: `LucyAI` orquesta NLP, clasificación y generación de respuesta
- Persistencia: `ConversationDB` (SQLite) con índices y tablas `conversations`, `users`
- Configuración dinámica: `ConfigManager` observa cambios en `config/config.json`
- Extensiones: `plugins` con manager de carga segura
- Web/API: FastAPI con endpoints `/api/*` y UI estática

## Rendimiento
- p95 < 2s en hardware de consumo para consultas comunes
- Cache de clasificación y contexto reutilizable por sesión
- Índices por usuario y fecha para consultas rápidas

## Casos de uso
- Asistente personal local, privacidad conservadora
- Prototipado de flujos conversacionales
- Extensión por comandos para integraciones externas

## Seguridad
- CSRF y cookies `HttpOnly` para sesión
- Hash PBKDF2-HMAC-SHA256 con salt único por usuario
- Comparación constante y sanitización básica de entradas

## Accesibilidad y UI
- WCAG AA: contraste, estructura semántica, navegación por teclado
- Diseño responsive y contenedores semitransparentes sobre fondo unificado

## Licencia y derechos
- Uso personal y educativo. Consulte el README para detalles adicionales.