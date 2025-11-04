@echo off
REM Ejecutor de Lucy AI (Windows)
chcp 65001 > nul
setlocal

echo [Lucy] Preparando entorno...
REM Activar entorno virtual si existe
IF EXIST .\.venv\Scripts\activate.bat (
    call .\.venv\Scripts\activate.bat
)

REM Asegurar UTF-8 y rutas
set PYTHONUTF8=1
set PYTHONPATH=%CD%

echo [Lucy] Iniciando Lucy AI...
python lucy.py %*

echo.
echo [Lucy] Finalizado.
pause
endlocal
