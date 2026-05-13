@echo off
REM Script de lanzamiento para Sistema de Cheques (Windows)
REM Ejecuta sin mostrar consola (modo silencioso)

REM Verificar si existe entorno virtual
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    cd chequera_app
) else (
    cd chequera_app
)

REM Ejecutar la aplicación sin consola (pythonw.exe)
start /B pythonw main.py
