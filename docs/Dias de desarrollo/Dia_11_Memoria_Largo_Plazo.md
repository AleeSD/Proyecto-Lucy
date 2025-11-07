# Día 11 – Memoria a Largo Plazo

## Objetivos y Alcance
- Incorporar una memoria conversacional persistente que permita almacenar y recuperar contexto relevante.
- Utilizar embeddings para búsquedas semánticas top-k y ofrecer fallback si embeddings no están disponibles.
- Exponer una API interna y comandos `!mem` en `LucyAI` para insertar, consultar y purgar memoria.
- Alinear métricas (latencia p95, recall@k) con las convenciones del proyecto y no romper pruebas existentes.

## Arquitectura Propuesta
- Componentes:
  - `ConversationDB`: almacén de eventos conversacionales con esquema estructurado.
  - `EmbeddingsProvider`: obtiene vectores para contenido y consultas.
  - `VectorIndex`: índice (FAISS/NearestNeighbors) para similitud y recuperación top-k.
  - `MemoryManager`: orquesta inserción, consulta, purga y manejo de fallback.
  - Integración con `LucyAI.process_message` vía comandos `!mem`.
- Flujo (alto nivel):
  - Inserción: `LucyAI` → `MemoryManager.add_event` → `EmbeddingsProvider.encode` → `ConversationDB` + `VectorIndex.add`.
  - Consulta: `LucyAI` → `MemoryManager.find_similar(query, top_k)` → `encode(query)` → `VectorIndex.search` → resultados con metadatos.
  - Purga: `LucyAI` → `MemoryManager.purge_conversation` → DB + índice.

## Esquema de Datos (ConversationDB)
- Campos sugeridos:
  - `conversacion_id` (string)
  - `usuario_id` (string)
  - `timestamp` (ISO8601)
  - `contenido` (text)
  - `embedding` (vector opcional; almacenado o derivable)
  - `metadatos` (json: `origen`, `idioma`, `canal`, `tags`)
  - `version_esquema` (int)
  - Índices recomendados: por `conversacion_id`, `usuario_id`, `timestamp`.

## Configuración (config/config.json)
- Claves propuestas:
  - `memory.enabled`: `true|false` (habilita el sistema)
  - `memory.provider`: `"faiss" | "sklearn" | "none"` (índice vectorial)
  - `memory.index_path`: ruta para persistir índice (si aplica)
  - `memory.top_k`: entero (p. ej., 5)
  - `memory.ttl_days`: entero opcional (retención)
  - `embeddings.model`: nombre del modelo (p. ej., `sentence-transformers/all-MiniLM-L6-v2`)
  - `privacy.mask_emails`: `true|false` (enmascarado básico de PII)
- Ejemplo:
```
{
  "advanced_nlp": { /* existente */ },
  "memory": {
    "enabled": true,
    "provider": "sklearn",
    "index_path": "data/models/memory_index",
    "top_k": 5,
    "ttl_days": 365
  },
  "embeddings": {
    "model": "sentence-transformers/all-MiniLM-L6-v2"
  },
  "privacy": {
    "mask_emails": true
  }
}
```

## API Interna (propuesta)
- `MemoryManager.add_event(conversacion_id, usuario_id, contenido, metadatos=None) -> str` (id del evento)
- `MemoryManager.find_similar(query, top_k=None, filtros=None) -> List[Resultado]`
  - `Resultado = {contenido, score, timestamp, conversacion_id, usuario_id, metadatos}`
- `MemoryManager.purge_conversation(conversacion_id) -> int` (número de registros purgados)
- `MemoryManager.rebuild_index() -> None`
- `MemoryManager.status() -> Dict` (tamaño de índice, proveedor, métricas mínimas)

## Comandos `!mem` en LucyAI
- Formato general: `!mem <accion> <param>=<valor> ...`
- Acciones soportadas:
  - `add text="..." conv_id=<id> user_id=<id> [tags=a,b]`
    - Inserta un evento en la memoria.
  - `find query="..." [top_k=5] [conv_id=<id>]`
    - Busca eventos similares y devuelve top-k resultados.
  - `purge conv_id=<id>`
    - Purga todos los eventos asociados a una conversación.
  - `status`
    - Devuelve proveedor de índice, tamaño y métricas básicas.
- Ejemplos:
  - `!mem add text="El pedido 123 fue entregado" conv_id=soporte user_id=juan`
  - `!mem find query="pedido 123 estado" top_k=3`
  - `!mem purge conv_id=soporte`
  - `!mem status`

## Integración con LucyAI
- Parsing en `LucyAI.process_message` del comando `!mem` y delegación en `MemoryManager`.
- Uso de memoria para enriquecer respuestas de `!nlp gen` (Día 16) y recomendaciones (Día 20).
- Respeto de configuración `memory.enabled` para activar/desactivar sin romper flujos actuales.

## Plan de Pruebas y Validación
- Unitarias:
  - Inserción y recuperación básica con proveedor `sklearn` (NearestNeighbors).
  - Purga por `conversacion_id` y verificación de tamaño del índice.
  - Fallback sin embeddings: búsqueda por keywords cuando `embeddings.model` no está disponible.
  - Enmascarado de PII: correos en contenido enmascarados cuando `privacy.mask_emails=true`.
- Integración:
  - Comandos `!mem` desde `LucyAI`: `add`, `find`, `purge`, `status`.
  - Latencia p95 < 150 ms en dataset de prueba (1000 eventos).
  - Recall@k ≥ 0.7 en consultas de validación.
- Cobertura:
  - Mantener umbral global de `pytest.ini` y añadir pruebas específicas de memoria.

## Métricas y Monitoreo
- `latencia_p95_busqueda`, `recall_k`, `tasa_insercion`, `tiempo_reconstruccion_indice`, `tasa_errores`.
- Log de eventos relevantes y contadores por acción (`add/find/purge`).

## Seguridad y Privacidad
- PII: enmascarado básico y/o hashing de identificadores sensibles.
- Cifrado en reposo (si el backend de DB lo soporta) y control de acceso.
- Políticas de retención (`ttl_days`) y purga segura.

## Riesgos y Mitigaciones
- Latencia y consistencia: elegir proveedor adecuado y validar p95; batch para reconstrucción.
- Almacenamiento: límites de tamaño y rotación; compresión opcional de embeddings.
- Privacidad: aplicar máscaras y retención; auditoría de acceso.

## Entregables
- Código: `MemoryManager`, proveedor de embeddings, índice vectorial y comandos `!mem` en `LucyAI`.
- Configuración: claves `memory.*`, `embeddings.*`, `privacy.*`.
- Pruebas: unitarias e integración para inserción/consulta/purga/fallback.
- Documentación: este documento y actualización en seguimiento semanal.

## Enlace con Seguimiento Semanal
- Estado y notas reflejadas en `docs/Semanas 2 y 3/Seguimiento_Progreso_y_Dependencias.md` (Día 11: en_progreso).
- Métricas añadidas en “Notas y Actualizaciones” para trazar latencia p95 y recall@k.

## Próximos Pasos
- Implementar `MemoryManager` y proveedores de índice (inicio con `sklearn`).
- Integrar comandos `!mem` en `LucyAI.process_message` y añadir pruebas.
- Evaluar FAISS como mejora de rendimiento; persistencia del índice.
- Añadir ADR para decisiones de modelos de embeddings e índices.