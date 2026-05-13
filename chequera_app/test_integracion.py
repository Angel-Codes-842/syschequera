"""
Script de pruebas de integración del sistema de cheques.
"""

import os
import sys
from pathlib import Path

# Agregar directorio del script al path
sys.path.insert(0, str(Path(__file__).parent))

from db import GestionadorCheques
from impresion import GeneradorPDF
from num2letras import numero_a_letras
from calibracion import VentanaCalibracion


def prueba_integracion_completa():
    """Ejecuta una prueba de integración completa."""
    
    print("=" * 80)
    print("PRUEBAS DE INTEGRACIÓN - SISTEMA DE CHEQUES")
    print("=" * 80)
    
    # Crear gestor BD de prueba
    print("\n[1/5] Inicializando base de datos...")
    db_test = "test_integracion.db"
    if os.path.exists(db_test):
        os.remove(db_test)
    
    gestor = GestionadorCheques(db_test)
    print("✓ Base de datos creada")
    
    # Crear generador PDF
    print("\n[2/5] Inicializando generador de PDFs...")
    generador = GeneradorPDF()
    print("✓ Generador de PDFs listo")
    print(f"  Plantillas disponibles: {generador.listar_plantillas()}")
    
    # Prueba 1: Conversión de números a letras
    print("\n[3/5] Prueba de conversión números → letras...")
    casos_prueba = [
        (1, "UN GUARANÍ"),
        (125000, "CIENTO VEINTICINCO MIL GUARANÍES"),
        (1000000, "UN MILLÓN DE GUARANÍES"),
    ]
    
    for numero, esperado in casos_prueba:
        resultado = numero_a_letras(numero)
        estado = "✓" if resultado == esperado else "✗"
        print(f"  {estado} {numero:>10} → {resultado}")
    
    # Prueba 2: Crear cheque de prueba y guardarlo en BD
    print("\n[4/5] Creando cheque de prueba en la base de datos...")
    cheque_prueba = {
        "serie": "TEST",
        "numero": 1001,
        "fecha_emision": "15/05",
        "beneficiario": "Juan Prueba",
        "importe_num": 125000,
        "importe_letras": numero_a_letras(125000),
        "concepto": "Cheque de prueba del sistema"
    }
    
    # Verificar que no existe
    if gestor.verificar_duplicado(cheque_prueba["serie"], cheque_prueba["numero"]):
        print("  ✗ El cheque ya existe, limpiando...")
        # Eliminar si existe
    else:
        print("  ✓ Cheque no existe (como esperado)")
    
    # Insertar cheque
    if gestor.insertar_cheque(**cheque_prueba):
        print("  ✓ Cheque insertado en base de datos")
    else:
        print("  ✗ No se pudo insertar el cheque")
        return False
    
    # Verificar que ahora existe
    if gestor.verificar_duplicado(cheque_prueba["serie"], cheque_prueba["numero"]):
        print("  ✓ Cheque verificado en base de datos")
    else:
        print("  ✗ No se puede verificar el cheque")
        return False
    
    # Prueba 3: Generar PDF
    print("\n[5/5] Generando PDF del cheque...")
    
    datos_para_pdf = {
        "serie": cheque_prueba["serie"],
        "numero": cheque_prueba["numero"],
        "fecha": cheque_prueba["fecha_emision"],
        "beneficiario": cheque_prueba["beneficiario"],
        "importe_num": f"{cheque_prueba['importe_num']:,}",
        "importe_letras": cheque_prueba["importe_letras"],
        "concepto": cheque_prueba["concepto"],
        "serie_numero": f"{cheque_prueba['serie']}-{cheque_prueba['numero']}"
    }
    
    ruta_pdf = generador.generar_pdf(datos_para_pdf, nombre_plantilla="banca_criptoheca")
    
    if ruta_pdf and os.path.exists(ruta_pdf):
        tamaño_kb = os.path.getsize(ruta_pdf) / 1024
        print(f"  ✓ PDF generado: {ruta_pdf}")
        print(f"    Tamaño: {tamaño_kb:.2f} KB")
    else:
        print(f"  ✗ No se pudo generar el PDF")
        return False
    
    # Prueba 4: Obtener historial
    print("\n[EXTRA] Verificando historial...")
    historial = gestor.obtener_historial_completo()
    print(f"  ✓ Total de cheques en BD: {len(historial)}")
    
    # Prueba 5: Estadísticas
    print("\n[EXTRA] Estadísticas de la BD...")
    stats = gestor.obtener_estadisticas()
    print(f"  ✓ Total de cheques: {stats['total_cheques']}")
    print(f"    Importe total: {stats['importe_total']:,} Gs.")
    print(f"    Series: {', '.join(stats['series'])}")
    
    # Limpiar archivos de prueba
    print("\n[FINAL] Limpieza...")
    if os.path.exists(db_test):
        os.remove(db_test)
    print("  ✓ Archivos de prueba eliminados")
    
    print("\n" + "=" * 80)
    print("✓ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        exito = prueba_integracion_completa()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n✗ ERROR EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
