# Guía de Deployment (Local) - Lucy AI

Este documento detalla cómo desplegar Lucy AI de forma confiable en Windows y Linux/macOS.

## Objetivo
Arranque reproducible con entorno virtual, dependencias instaladas, configuración lista y scripts de servicio.

## Windows (PowerShell)
1. Clonar y preparar entorno:
```powershell
git clone <url>
cd Proyecto-Lucy
scripts\setup_env.ps1
```
2. Configurar `config/config.json` según tus rutas.
3. Probar y validar:
```powershell
pytest -q --cov=src/lucy --cov-report=term-missing
```
4. Ejecutar:
```powershell
run_lucy.bat
```

## Linux/macOS
1. Clonar y preparar entorno:
```bash
git clone <url>
cd Proyecto-Lucy
bash scripts/setup_env.sh
```
2. Configurar `config/config.json`.
3. Validar:
```bash
pytest -q --cov=src/lucy --cov-report=term-missing
```
4. Ejecutar:
```bash
bash run_lucy.sh
```

## Buenas prácticas
- Mantener `data/intents/*` y `data/models/*` versionados o gestionados.
- Configurar rotación de logs y revisión periódica de `logs/*`.
- Respaldar `data/conversations.db` regularmente.

## Servicios (opcional)
- Windows: usar `Task Scheduler` para arranque automático del script.
- Linux: crear unidad `systemd` para ejecutar `run_lucy.sh` bajo usuario.

## Troubleshooting de deployment
- Faltan modelos: entrenar con `python -m src.lucy.training` o usar modo básico.
- Permisos de escritura: verificar rutas en `config/config.json`.
- Timeouts o latencia alta: revisar métricas en `logs/performance/performance.log`.