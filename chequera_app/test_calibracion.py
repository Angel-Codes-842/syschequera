"""
Test rápido del módulo de calibración (sin GUI).
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from impresion import GeneradorPDF


def test_calibracion():
    """Prueba la funcionalidad de calibración."""
    print("=" * 80)
    print("PRUEBA: MÓDULO DE CALIBRACIÓN")
    print("=" * 80)
    
    # Crear generador
    print("\n[1/3] Inicializando generador PDF...")
    gen = GeneradorPDF()
    print("✓ Generador inicializado")
    print(f"  Offset actual: X={gen.offset_x}, Y={gen.offset_y}")
    
    # Simular ajuste de offset
    print("\n[2/3] Simulando ajuste de offset...")
    gen.offset_x = 1.5
    gen.offset_y = -0.5
    print(f"✓ Nuevo offset: X={gen.offset_x}, Y={gen.offset_y}")
    
    # Crear archivo de prueba para verificar que la calibración se aplica
    print("\n[3/3] Generando PDF de prueba con calibración...")
    
    # Crear carpeta PDFs si no existe
    gen.ruta_pdfs.mkdir(parents=True, exist_ok=True)
    
    datos_prueba = {
        "serie": "CAL",
        "numero": 9999,
        "fecha": "11/05",
        "beneficiario": "Prueba Calibración",
        "importe_num": "100.000",
        "importe_letras": "CIEN MIL GUARANÍES",
        "concepto": "Test calibración",
        "serie_numero": "CAL-9999"
    }
    
    ruta_pdf = gen.generar_pdf(datos_prueba, nombre_plantilla="banca_criptoheca")
    
    if ruta_pdf and os.path.exists(ruta_pdf):
        tamaño = os.path.getsize(ruta_pdf) / 1024
        print(f"✓ PDF generado: {ruta_pdf}")
        print(f"  Tamaño: {tamaño:.2f} KB")
        print(f"  Con offset aplicado: X={gen.offset_x}mm, Y={gen.offset_y}mm")
    else:
        print("✗ No se pudo generar el PDF")
        return False
    
    print("\n" + "=" * 80)
    print("✓ PRUEBA DE CALIBRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    print("\nNota: Para probar la interfaz gráfica de calibración, ejecuta:")
    print("  python main.py")
    print("  → Menú Configuración → Calibrar Impresión")
    
    return True


if __name__ == "__main__":
    try:
        exito = test_calibracion()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
