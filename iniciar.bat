@echo off
REM Script de lanzamiento para Sistema de Cheques (Windows)
REM Verifica e instala dependencias automáticamente antes de ejecutar

set DIR_APP=%~dp0
cd /d "%DIR_APP%"

REM Verificar que Python existe
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python no esta instalado o no esta en el PATH.
    echo Instala Python 3.10 o superior desde https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Instalar/verificar dependencias (pip omite las ya instaladas)
echo Verificando dependencias...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo ERROR: No se pudieron instalar las dependencias.
    echo Verifica tu conexion a internet e intenta de nuevo.
    pause
    exit /b 1
)

REM Ejecutar la aplicacion
cd /d "%DIR_APP%\chequera_app"
start /B pythonw main.py
