# Día 10 – PLN Avanzado

Este día añade un gestor ligero de PLN avanzado para enriquecer el procesamiento con análisis de sentimiento, extracción de entidades y palabras clave, y un comando directo desde LucyAI.

## Objetivos
- Incorporar `AdvancedNLPManager` con análisis configurable.
- Añadir comando `!nlp` para invocar análisis ad-hoc.
- Enriquecer el contexto conversacional con resultados de análisis.
- Actualizar configuración con `advanced_nlp`.
- Crear pruebas unitarias.

## Arquitectura
- `src/lucy/nlp/manager.py`: gestor central de PLN, sin dependencias externas pesadas.
- `src/lucy/nlp/__init__.py`: exporta `AdvancedNLPManager`.
- `src/lucy/lucy_ai.py`: inicializa el gestor y maneja `!nlp`.

## Configuración
Se añadió la sección `advanced_nlp` en `config/config.json`:

```json
"advanced_nlp": {
  "enabled": true,
  "keywords": {"top_n": 5}
}
```

## Comando en LucyAI
Formato: `!nlp analyze text=...`

Ejemplo: `!nlp analyze text=Me siento feliz hoy`

El resultado se devuelve en JSON y puede incluir:
- `sentiment`: `score`, `label`, `pos`, `neg`
- `entities`: `emails`, `dates`, `numbers`
- `keywords`: lista de términos frecuentes sin stopwords

## Pruebas
- `tests/test_nlp.py` valida sentimiento (positivo/negativo) y entidades.

## Criterios de Aceptación
- AdvancedNLPManager instanciado cuando `advanced_nlp.enabled=true`.
- LucyAI soporta el comando `!nlp` y devuelve JSON de análisis.
- Pruebas unitarias pasan sin romper el resto del suite.

## Próximos pasos
- Añadir extracción de entidades más rica (personas, lugares) con modelos opcionales.
- Integrar análisis automático en `process_message` para personalización avanzada.
- Métricas de sentimiento y palabras clave por sesión.