# Progreso Diario – Día 7: Documentación y Deployment

## Resumen del día
- Se actualizó `README.md` con instalación rápida, ejecución, pruebas y cobertura.
- Se añadieron guías dedicadas:
  - `docs/Guia_Instalacion.md`
  - `docs/Guia_Ejecucion.md`
  - `docs/Guia_Deployment.md`
- Se mejoraron los scripts de ejecución `run_lucy.bat` y `run_lucy.sh` para activar el venv automáticamente y configurar el entorno (UTF-8 y `PYTHONPATH`).
- Se agregaron scripts de preparación de entorno:
  - `scripts/setup_env.ps1` (Windows)
  - `scripts/setup_env.sh` (Linux/Mac)

## Validación
- Pruebas: `pytest -q` y `pytest -q --cov=src/lucy --cov-report=term-missing` ejecutan correctamente.
- Cobertura informada en consola y umbral configurable en `pytest.ini`.
- Ejecución local ok en Windows y Linux con venv.

## Desviaciones / Bloqueos
- `core/` se mantiene como alias temporal, pero se promueve `src/lucy` en documentación y comandos.
- Scripts nuevos evitan suposiciones del entorno y priorizan reproducibilidad.

## Próximos pasos
- Añadir guía de troubleshooting ampliada (NLTK, TF, permisos, rutas).
- Crear ejemplo de unidad `systemd` para servicio opcional en Linux.
- Generar assets de modelos de ejemplo bajo `src/test_models/` para demos.