# Sistema de Emisión de Cheques

Aplicación de escritorio para emitir y gestionar cheques digitales con impresión computarizada.

## Características

✅ **Conversión automática de importes a letras** — Números a guaraní en mayúsculas  
✅ **Generación de PDFs posicionados** — Basados en plantillas JSON configurables  
✅ **Base de datos SQLite** — Historial de cheques emitidos  
✅ **Interfaz gráfica Tkinter** — Intuitiva y fácil de usar  
✅ **Impresión directa** — Enviar a impresora o vista previa  
✅ **Múltiples plantillas** — Soporta diferentes bancos/formatos  
✅ **Calibración de impresión** — Ajuste de offset global  
✅ **Filtrado de historial** — Por serie, número y fecha  

## Requisitos

- **Python 3.10+**
- **Dependencias:**
  - `reportlab` — Generación de PDFs
  - `tkcalendar` — Date picker en la interfaz

## Instalación

### 1. Clonar/Descargar el proyecto
```bash
git clone <repo-url>
cd syschequera
```

### 2. Instalar dependencias
```bash
pip install reportlab tkcalendar
```

### 3. Ejecutar la aplicación

**Windows (recomendado):**
```batch
# Doble clic en iniciar.vbs (ejecuta sin consola)
iniciar.vbs
```

**macOS/Linux:**
```bash
chmod +x iniciar.sh
./iniciar.sh
```

**Manual:**
```bash
cd chequera_app
python main.py
```

## Estructura del Proyecto

```
syschequera/
├── plan.md                          # Plan del proyecto
├── chequera_app/
│   ├── main.py                      # Aplicación principal (Tkinter)
│   ├── num2letras.py                # Conversión números → letras
│   ├── db.py                        # Gestión de base de datos SQLite
│   ├── impresion.py                 # Generación e impresión de PDFs
│   ├── calibracion.py               # Ventana interactiva de calibración
│   ├── config.json                  # Configuración global
│   ├── cheques.db                   # Base de datos (generada automáticamente)
│   ├── plantillas/                  # Carpeta de plantillas JSON
│   │   └── banca_criptoheca.json    # Plantilla de ejemplo
│   ├── PDFs/                        # Carpeta de PDFs generados (generada automáticamente)
│   └── test_integracion.py          # Script de pruebas
```

## Módulos

### `num2letras.py`
Convierte números enteros a letras en guaraní (mayúsculas).

**Ejemplo:**
```python
from num2letras import numero_a_letras

resultado = numero_a_letras(125000)
# Retorna: "CIENTO VEINTICINCO MIL GUARANÍES"
```

### `db.py`
Gestiona la base de datos SQLite con tabla `cheques`.

**Ejemplo:**
```python
from db import GestionadorCheques

gestor = GestionadorCheques("cheques.db")
gestor.insertar_cheque("CD", 1001, "15/05", "Juan Pérez", 125000, "CIENTO...", "Concepto")
historial = gestor.obtener_historial_completo()
```

### `impresion.py`
Genera PDFs y envía a imprimir.

**Ejemplo:**
```python
from impresion import GeneradorPDF

gen = GeneradorPDF()
datos = {
    "serie": "CD",
    "numero": 1001,
    "fecha": "15/05",
    "beneficiario": "Juan Pérez",
    "importe_num": "125.000",
    "importe_letras": "CIENTO VEINTICINCO MIL GUARANÍES",
    "concepto": "Pago de servicios"
}
ruta_pdf = gen.generar_pdf(datos)
gen.abrir_vista_previa(ruta_pdf)
```

### `calibracion.py`
Ventana interactiva para calibrar impresión.

**Características:**
- Ajustar offset X, Y con botones o entrada directa
- Generar PDF de prueba con líneas de referencia (cada 10mm)
- Guardar calibración en config.json
- Resetear a 0

**Uso desde main.py:**
```python
from calibracion import VentanaCalibracion

# En el menú de Configuración
VentanaCalibracion(ventana_padre, generador_pdf)
```
Aplicación gráfica principal con dos pestañas:

**Pestaña 1: Ingreso de Cheque**
- Selector de plantilla
- Campos: Serie, Número, Fecha (date picker), Beneficiario, Importe
- Conversión automática de importe a letras
- Botones: Vista Previa, Imprimir, Guardar, Limpiar

**Pestaña 2: Historial**
- Tabla de cheques emitidos
- Filtros: Por serie, rango de números
- Botones: Filtrar, Limpiar Filtros, Recargar (F5)

## Configuración

Edita `config.json` para personalizar:

```json
{
  "offset_x": 0,              // Ajuste horizontal en mm (para calibración)
  "offset_y": 0,              // Ajuste vertical en mm (para calibración)
  "plantilla_actual": "banca_criptoheca",  // Plantilla por defecto
  "ruta_plantillas": "./plantillas",       // Carpeta de plantillas
  "ruta_pdfs": "./PDFs",                   // Carpeta de salida de PDFs
  "ruta_bd": "cheques.db",                 // Ubicación de BD
  "impresora_predeterminada": "",          // Nombre de impresora (vacío = predeterminada)
  "tamaño_fuente_default": 11              // Tamaño de fuente en puntos
}
```

## Plantillas JSON

Las plantillas definen las coordenadas (X, Y en mm) donde se posicionarán los campos en el cheque.

**Estructura:**
```json
{
  "nombre": "Banca Criptoheca",
  "banco": "Banca Criptoheca",
  "ancho_mm": 210,
  "alto_mm": 99,
  "campos": {
    "fecha": { "x": 165, "y": 15, "tamaño": 10, "alineacion": "derecha" },
    "beneficiario": { "x": 20, "y": 50, "tamaño": 11, "alineacion": "izquierda" },
    "importe_num": { "x": 175, "y": 45, "tamaño": 11, "alineacion": "derecha" },
    "importe_letras": { "x": 20, "y": 70, "tamaño": 10, "alineacion": "izquierda" },
    "concepto": { "x": 20, "y": 85, "tamaño": 9, "alineacion": "izquierda" },
    "serie_numero": { "x": 175, "y": 90, "tamaño": 10, "alineacion": "derecha" }
  }
}
```

Para agregar una nueva plantilla:
1. Crear archivo `plantillas/nombre_banco.json`
2. Definir las coordenadas exactas de los campos
3. En `main.py`, seleccionar la plantilla del combo

## Uso

### Flujo básico

1. **Abrir la aplicación:** `python main.py`
2. **Pestaña "Ingreso de Cheque":**
   - Seleccionar plantilla
   - Ingresar serie, número, fecha, beneficiario, importe
   - El importe en letras se genera automáticamente
   - Ingresar concepto (opcional)
3. **Opciones:**
   - **Vista Previa:** Ver PDF antes de guardar
   - **Imprimir:** Enviar directamente a impresora
   - **Guardar:** Guardar cheque en BD + generar PDF
4. **Historial:**
   - Ver todos los cheques emitidos
   - Filtrar por serie o rango de números
   - Refrescar con F5

#### Calibración de Impresión

Si los campos no se alinean correctamente con el papel:

1. **En la aplicación:** Menú → Configuración → Calibrar Impresión
2. **En la ventana de calibración:**
   - Ajustar **Offset X** (horizontal) y **Offset Y** (vertical)
   - Usar los botones ← → ↑ ↓ o ingresar valores directamente
   - Cambiar el "Paso" para incrementos más grandes/pequeños (0.1 - 5mm)
3. **Generar PDF de prueba:** Botón "Generar PDF de Prueba"
   - Se abrirá un PDF con líneas de referencia cada 10mm
   - Imprimir y comparar con papel preimpreso
4. **Ajustar iterativamente:**
   - Si campos están a la derecha → Offset X negativo
   - Si campos están arriba → Offset Y negativo
5. **Guardar:** Botón "Guardar Calibración" (se guarda en config.json)

**Alternativa manual:** Editar directamente `config.json`:
```json
{
  "offset_x": 0.5,    // en mm (positivo = derecha, negativo = izquierda)
  "offset_y": -0.3    // en mm (positivo = arriba, negativo = abajo)
}
```

## Base de Datos

La BD se crea automáticamente en `cheques.db` con la tabla:

```sql
CREATE TABLE cheques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serie TEXT NOT NULL,
    numero INTEGER NOT NULL,
    fecha_emision TEXT,           -- formato dd/mm
    beneficiario TEXT NOT NULL,
    importe_num INTEGER NOT NULL,
    importe_letras TEXT NOT NULL,
    concepto TEXT DEFAULT '',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(serie, numero)         -- Previene cheques duplicados
);
```

## Pruebas

Ejecutar pruebas de integración:
```bash
cd chequera_app
python test_integracion.py
```

Expected output:
```
================================================================================
✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE
================================================================================
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| "tkcalendar no instalado" | `pip install tkcalendar` |
| "reportlab no instalado" | `pip install reportlab` |
| PDF no se abre | Verificar ruta en `config.json` → `ruta_pdfs` |
| Campos desalineados | Ajustar `offset_x` y `offset_y` en `config.json` |
| Cheque duplicado | La BD rechaza serie+número repetidos (por diseño) |
| Impresora no responde | Verificar nombre en `config.json` → `impresora_predeterminada` |

## Desarrollo Futuro

- [ ] Exportar historial a CSV/Excel
- [ ] Estadísticas y reportes
- [ ] Validación automática de checksum de cheques
- [ ] Backup automático de BD
- [ ] Más plantillas de bancos
- [ ] Firma digital en PDFs
- [ ] Interfaz web (Flask/FastAPI)

## Licencia

Este proyecto está disponible bajo licencia MIT.

## Autor

Desarrollo: 2026

---

**¿Preguntas?** Consulta el archivo `plan.md` para más detalles técnicos.
