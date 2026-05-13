#!/bin/bash
# Script de lanzamiento para Sistema de Cheques (macOS/Linux)

echo "Iniciando Sistema de Cheques..."

# Verificar si existe entorno virtual
if [ -f "venv/bin/activate" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
    cd chequera_app
else
    echo "Entorno virtual no encontrado, usando Python global..."
    cd chequera_app
fi

# Ejecutar la aplicación
python3 main.py

# Si hubo error, pausar
if [ $? -ne 0 ]; then
    echo ""
    echo "Error al iniciar la aplicación."
    read -p "Presione Enter para salir..."
fi
