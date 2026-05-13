# Guía de Deployment - Sistema de Cheques

## Requisitos del Sistema

- **Python**: 3.10 o superior
- **Sistema Operativo**: Windows, macOS o Linux
- **Memoria RAM**: Mínimo 2 GB
- **Espacio en disco**: 100 MB (sin contar PDFs generados)

## Instalación

### 1. Clonar o copiar el proyecto

```bash
# Si está en un repositorio
git clone <url-repositorio>
cd syschequera

# O copiar la carpeta del proyecto
```

### 2. Crear entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
cd chequera_app
pip install -r ../requirements.txt
```

Las dependencias requeridas son:
- `reportlab==4.0.7` - Generación de PDFs
- `tkcalendar` - Selector de fecha (opcional, usa fallback si no está)
- `pywin32==305` - Funciones de Windows (solo Windows)
- `pytest==7.4.3` - Tests (solo desarrollo)

### 4. Verificar instalación

```bash
cd chequera_app
python monitoreo.py
```

Debe mostrar un reporte de health checks con todos los ítems en verde (✓).

## Configuración

### Archivo de configuración

El archivo `config.json` se genera automáticamente con valores por defecto. Ubicación:
- `chequera_app/config.json`

### Configuración inicial

1. **Plantillas**: Coloque los archivos JSON de plantillas en `chequera_app/plantillas/`
2. **Impresora**: Configure la impresora predeterminada desde la interfaz
3. **Calibración**: Use la herramienta de calibración para ajustar los offsets de impresión

### Estructura de directorios

```
syschequera/
├── chequera_app/
│   ├── main.py              # Aplicación principal
│   ├── db.py                # Gestión de base de datos
│   ├── impresion.py         # Generación de PDFs
│   ├── backup.py            # Sistema de backups
│   ├── migraciones.py       # Migraciones de schema
│   ├── config.py            # Configuración centralizada
│   ├── monitoreo.py         # Health checks
│   ├── calibracion.py       # Herramienta de calibración
│   ├── num2letras.py        # Conversión números a letras
│   ├── config.json          # Configuración (generado automáticamente)
│   ├── cheques.db           # Base de datos SQLite
│   ├── plantillas/          # Plantillas de cheques JSON
│   ├── PDFs/                # PDFs generados (organizados por mes)
│   ├── temp/                # Archivos temporales
│   ├── backups/             # Backups automáticos de BD
│   └── tests/               # Tests unitarios
├── requirements.txt         # Dependencias
├── DEPLOYMENT.md           # Esta guía
└── README.md               # Documentación general
```

## Ejecución

### Iniciar la aplicación

#### Método 1: Scripts de lanzamiento (recomendado)

**Windows:**
```batch
# Opción 1: Ejecutar sin consola (recomendado)
# Doble clic en iniciar.vbs (ejecuta completamente oculto)
iniciar.vbs

# Opción 2: Ejecutar con ventana mínima
# Doble clic en iniciar.bat
iniciar.bat
```

**macOS/Linux:**
```bash
# Dar permisos de ejecución primero
chmod +x iniciar.sh

# Ejecutar
./iniciar.sh
```

#### Método 2: Manual

```bash
cd chequera_app
python main.py
```

### Ejecutar tests

```bash
cd chequera_app
python -m pytest tests/ -v
```

### Verificar estado del sistema

```bash
cd chequera_app
python monitoreo.py
```

## Gestión de Backups

### Backups automáticos

El sistema crea backups automáticos después de cada inserción de cheque:
- Ubicación: `chequera_app/backups/`
- Formato: `cheques_backup_YYYYMMDD_HHMMSS_ffffff.db`
- Rotación: Máximo 10 backups (configurable en `config.json`)

### Restaurar backup manualmente

```python
from backup import GestorBackup

gestor = GestorBackup("cheques.db", max_backups=10)
gestor.restaurar_backup("ruta/al/backup.db")
```

## Migraciones de Base de Datos

El sistema aplica migraciones automáticamente al iniciar. Las migraciones se almacenan en:
- `chequera_app/migraciones/` (generado automáticamente)

### Crear nueva migración

```python
from migraciones import GestorMigraciones

gestor = GestorMigraciones("cheques.db")
gestor.crear_migracion(2, "descripcion", "SQL_AQUI")
```

## Solución de Problemas

### Error: "No se requiere reportlab"

**Solución**: Instalar reportlab
```bash
pip install reportlab
```

### Error: "Base de datos bloqueada"

**Causa**: La base de datos está siendo usada por otra instancia.

**Solución**: Cierre todas las instancias de la aplicación y reintente.

### Error: "No se puede abrir la carpeta"

**Causa**: Permisos insuficientes o ruta incorrecta.

**Solución**: Verifique permisos y que las carpetas existan.

### PDFs no se alinean correctamente

**Solución**: Use la herramienta de calibración:
1. Abra la aplicación
2. Menú: Herramientas → Calibración
3. Genere un PDF de prueba
4. Ajuste los offsets X e Y
5. Guarde la calibración

## Actualización del Sistema

### Actualizar dependencias

```bash
pip install -r requirements.txt --upgrade
```

### Actualizar código

1. Haga backup de `cheques.db` y `config.json`
2. Reemplace los archivos del código
3. Ejecute `python monitoreo.py` para verificar
4. Ejecute los tests: `python -m pytest tests/ -v`

## Seguridad

### Recomendaciones

1. **Permisos de archivo**: Asegure que `cheques.db` tenga permisos restringidos
2. **Backups**: Mantenga copias de backups fuera del directorio de la aplicación
3. **Redes**: No exponga la aplicación en redes públicas (es una app de escritorio)

### Notas

- El sistema NO incluye autenticación (según requisitos)
- El sistema NO incluye encriptación (según requisitos)
- El sistema NO incluye logging (según requisitos)

## Soporte

Para problemas o preguntas:
1. Ejecute `python monitoreo.py` para diagnosticar
2. Revise los tests: `python -m pytest tests/ -v`
3. Consulte el README.md para documentación general

## Checklist de Deployment

- [ ] Python 3.10+ instalado
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Health checks pasan (`python monitoreo.py`)
- [ ] Tests pasan (`python -m pytest tests/ -v`)
- [ ] Directorios creados (PDFs, plantillas, temp, backups)
- [ ] Configuración inicial realizada
- [ ] Impresora configurada
- [ ] Calibración realizada
- [ ] Backup inicial creado manualmente

## Script de Instalación Rápida (Windows)

```batch
@echo off
echo Instalando Sistema de Cheques...

REM Crear entorno virtual
python -m venv venv
call venv\Scripts\activate

REM Instalar dependencias
cd chequera_app
pip install -r ../requirements.txt

REM Verificar instalación
python monitoreo.py

echo.
echo Instalación completada. Ejecute 'python main.py' para iniciar.
pause
```

## Script de Instalación Rápida (macOS/Linux)

```bash
#!/bin/bash
echo "Instalando Sistema de Cheques..."

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
cd chequera_app
pip install -r ../requirements.txt

# Verificar instalación
python monitoreo.py

echo ""
echo "Instalación completada. Ejecute 'python main.py' para iniciar."
```
