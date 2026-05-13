# Software de Emisión de Cheques – Documento de Proyecto

## 1. Resumen del Proyecto
Desarrollar una aplicación de escritorio que reemplace el llenado manual de cheques por impresión computarizada. La firma seguirá siendo manual. El sistema debe ser configurable para distintos formatos de cheques (diferentes bancos o cuentas) mediante plantillas.

**Contexto objetivo:**
- El banco acepta cheques impresos.
- Un solo usuario, sin necesidad de control de acceso ni multiusuario.
- Solo se imprime el cuerpo del cheque (no se calcula ni imprime el saldo del talón).
- Importes siempre en guaraníes enteros (sin decimales).
- Requiere guardar historial de cheques emitidos (series y números).

## 2. Requerimientos Funcionales
1. **Selección de plantilla de cheque**  
   - Cada modelo de cheque se define en un archivo JSON con las coordenadas exactas de los campos.
2. **Ingreso de datos**  
   - Serie (alfanumérico, ej. "CD")  
   - Número de cheque (entero)  
   - Fecha de emisión (día/mes)  
   - Beneficiario ("Páguese a la orden de")  
   - Importe en números (entero)  
   - Importe en letras (generado automáticamente por el sistema)  
   - Concepto (opcional)
3. **Conversión automática de importe a letras**  
   - Guaraníes, enteros, en mayúsculas.  
   - Ejemplo: `125.000` → `CIENTO VEINTICINCO MIL GUARANÍES`
4. **Vista previa e impresión**  
   - Generar un PDF con los datos posicionados en las coordenadas indicadas por la plantilla.  
   - El PDF no debe contener fondo; se imprime directamente sobre el papel del cheque preimpreso.
5. **Historial de cheques emitidos**  
   - Almacenar en base de datos local: serie, número, fecha, beneficiario, importe, concepto, importe en letras.
   - Poder consultar y filtrar el historial.
   - Evitar duplicados: la combinación `serie + número` debe ser única.
6. **Calibración de impresión**  
   - Permitir ajustar un offset global (X, Y en mm) para compensar diferencias entre impresoras, sin modificar las plantillas.

## 3. Stack Tecnológico
- **Lenguaje:** Python 3.10+
- **Interfaz gráfica:** Tkinter (incluido en Python)
- **Generación de PDF:** `reportlab`
- **Base de datos:** SQLite3 (módulo estándar)
- **Configuración:** archivos JSON (`config.json` para offset global) y una carpeta `plantillas/` con un JSON por modelo de cheque.

## 4. Modelo de Datos (SQLite)
Se usará una única tabla `cheques`:

```sql
CREATE TABLE IF NOT EXISTS cheques (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    serie TEXT NOT NULL,
    numero INTEGER NOT NULL,
    fecha_emision TEXT NOT NULL,          -- formato dd/mm
    beneficiario TEXT NOT NULL,
    importe_num INTEGER NOT NULL,
    importe_letras TEXT NOT NULL,
    concepto TEXT DEFAULT '',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(serie, numero)
);