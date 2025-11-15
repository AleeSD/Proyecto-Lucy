# Información técnica de Lucy AI

## Capacidades
- PLN multilingüe (es/en), normalización y lematización con NLTK
- Clasificación de intenciones con TensorFlow; fallback por reglas cuando la confianza es baja
- Plugins/Servicios extensibles con límites y aislamiento
- Memoria contextual y recuperación por embeddings
- Observabilidad: métricas de latencia, logging estructurado, trazas de conversación
 - Autocompletado de mensajes y detección robusta de intención
 - Configuración dinámica (watcher) y perfiles de uso

## Arquitectura
- Núcleo: `LucyAI` orquesta NLP, clasificación y generación de respuesta
- Persistencia: `ConversationDB` (SQLite) con índices y tablas `conversations`, `users`
- Configuración dinámica: `ConfigManager` observa cambios en `config/config.json`
- Extensiones: `plugins` con manager de carga segura
- Web/API: FastAPI con endpoints `/api/*` y UI estática
 - Servicios externos: clientes desacoplados y reintentos, cache por servicio
 - Integración híbrida opcional con Django para administración (`/django/admin`)

## Rendimiento
- p95 < 2s en hardware de consumo para consultas comunes
- Cache de clasificación y contexto reutilizable por sesión
- Índices por usuario y fecha para consultas rápidas
 - Métricas y benchmarks sugeridos; cobertura objetivo ≥ 85%

## Casos de uso
- Asistente personal local, privacidad conservadora
- Prototipado de flujos conversacionales
- Extensión por comandos para integraciones externas
 - Laboratorio educativo con auditoría y métricas

## Seguridad
- CSRF y cookies `HttpOnly` para sesión
- Hash PBKDF2-HMAC-SHA256 con salt único por usuario
- Comparación constante y sanitización básica de entradas
 - Rate limiting y CORS configurables

## Accesibilidad y UI
- WCAG AA: contraste, estructura semántica, navegación por teclado
- Diseño responsive y contenedores semitransparentes sobre fondo unificado
 - Sidebar en inicio unida visualmente al header, con atajos a secciones
 - Tarjeta de información ampliada para mayor legibilidad

## Sidebar de Inicio (Atajos de Información)
- La página principal incluye una barra lateral vertical para atajos a las secciones de información.
- Enlaces: `#capabilities`, `#architecture`, `#performance`, `#use-cases`, `#roadmap`, `#release-notes`, `#author`, `#published`, `#license`.
- Diseño: ancho fijo (~280px) en desktop, fondo semitransparente y bordes acorde al sistema.
- Reserva: bloque de expansión equivalente al 30% del área para futuras opciones.
- Responsive: en ≤900px se apila por encima del contenido principal.
- Código relacionado: `src/lucy/web/static/index.html:24-47` y `src/lucy/web/static/assets/styles.css:133-151`.

### Contenido ampliado del inicio
- Capacidades: se incluyen detalles de autocompletado, perfiles de configuración, y manejo de idiomas.
- Arquitectura: se describen capas de plugins, servicios desacoplados con reintentos, memoria semántica y protección CSRF en FastAPI.
- Rendimiento: se añaden métricas objetivo, cache por sesión, y recomendaciones de optimización visual.
- Casos de uso: se amplían escenarios educativos y de auditoría con trazabilidad.
- Roadmap: se menciona integración híbrida con Django para administración y futuras analíticas.
- Notas de release: registro de cambios visibles en UI (sidebar, opacidad, accesibilidad) y mejoras de seguridad.

## Licencia y derechos
- Uso personal y educativo. Consulte el README para detalles adicionales.