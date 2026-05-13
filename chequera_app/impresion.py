"""
Módulo de generación de PDFs para cheques.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from config import obtener_config
import subprocess
import sys

# Intentar importar ReportLab, si no está, sugerir instalación
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from reportlab.lib.pagesizes import A4, landscape, portrait
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("ERROR: Se requiere instalar ReportLab")
    print("Ejecuta: pip install reportlab")
    sys.exit(1)


class GeneradorPDF:
    """Genera PDFs de cheques basados en plantillas JSON."""
    
    def __init__(self, ruta_config: str = None):
        """
        Inicializa el generador de PDFs.
        
        Args:
            ruta_config: Ruta del archivo config.json (default: usa configuración centralizada)
        """
        # Usar configuración centralizada
        self.config_mgr = obtener_config(ruta_config, str(Path(__file__).parent))
        self.config = self.config_mgr.a_dict()
        self.dir_base = self.config_mgr.dir_base
        self.ruta_plantillas = self.config_mgr.ruta_plantillas
        self.ruta_pdfs = self.config_mgr.ruta_pdfs
        self.ruta_temp = self.dir_base / "temp"
        self.offset_x = self.config_mgr.offset_x
        self.offset_y = self.config_mgr.offset_y
        
        # Crear carpetas si no existen
        self.ruta_pdfs.mkdir(parents=True, exist_ok=True)
        self.ruta_temp.mkdir(parents=True, exist_ok=True)
        
        # Registrar fuente predeterminada
        self._registrar_fuentes()
    
    def _registrar_fuentes(self):
        """Registra fuentes personaliza das (si existen)."""
        try:
            # Intentar usar Helvetica (fuente estándar disponible)
            # ReportLab incluye fuentes estándar por defecto
            pass
        except (OSError, IOError) as e:
            print(f"Advertencia al registrar fuentes: {e}")
    
    def cargar_plantilla(self, nombre_plantilla: str) -> Optional[Dict]:
        """
        Carga una plantilla desde un archivo JSON.
        
        Args:
            nombre_plantilla: Nombre del archivo de plantilla (sin extensión)
        
        Returns:
            Diccionario con los datos de la plantilla o None si falla
        """
        ruta_plantilla = self.ruta_plantillas / f"{nombre_plantilla}.json"
        
        try:
            with open(ruta_plantilla, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Plantilla {ruta_plantilla} no encontrada")
            return None
        except json.JSONDecodeError as e:
            print(f"ERROR al parsear plantilla: {e}")
            return None
    
    def listar_plantillas(self) -> list:
        """Lista todas las plantillas disponibles."""
        if not self.ruta_plantillas.exists():
            return []
        
        plantillas = [f.stem for f in self.ruta_plantillas.glob("*.json")]
        return sorted(plantillas)
    
    def generar_pdf(self, datos_cheque: Dict, archivo_salida: Optional[str] = None,
                   nombre_plantilla: Optional[str] = None, es_temporal: bool = False) -> Optional[str]:
        """
        Genera un PDF del cheque basado en una plantilla.
        
        Args:
            datos_cheque: Diccionario con los datos del cheque
            archivo_salida: Ruta donde guardar el PDF (default: generada automáticamente)
            nombre_plantilla: Nombre de la plantilla a usar (default: de config.json)
            es_temporal: Si es True, guarda en la carpeta temp para vista previa
        
        Returns:
            Ruta del PDF generado o None si falla
        """
        # Determinar plantilla
        if not nombre_plantilla:
            nombre_plantilla = self.config.get("plantilla_actual", "Continental")
        
        plantilla = self.cargar_plantilla(nombre_plantilla)
        if not plantilla:
            return None
        
        # Generar ruta de salida si no se proporciona
        if not archivo_salida:
            if es_temporal:
                # Nombre fijo para vista previa para no acumular archivos
                archivo_salida = str(self.ruta_temp / "vista_previa_cheque.pdf")
            else:
                archivo_salida = self._generar_ruta_pdf(
                    datos_cheque["serie"],
                    datos_cheque["numero"]
                )
        
        # Crear carpeta si es necesario
        Path(archivo_salida).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Usar tamaño A4 estándar (210 x 297 mm)
            # Esto soluciona problemas de orientación en la mayoría de las impresoras
            ancho_a4, alto_a4 = A4  # En puntos (1 mm = 2.834 pts)
            
            c = canvas.Canvas(archivo_salida, pagesize=A4)
            
            # El cheque se posicionará en la parte SUPERIOR de la hoja A4
            # Altura del cheque según plantilla
            alto_cheque_mm = plantilla.get("alto_mm", 76)
            
            # Convertir mm a puntos para el desplazamiento vertical
            # ReportLab usa (0,0) en la esquina inferior izquierda.
            # Para imprimir en el tope, el offset Y base es: Altura_A4 - Altura_Cheque
            offset_y_base_pts = alto_a4 - (alto_cheque_mm * mm)
            
            # Configurar fuente
            tamaño_fuente = self.config.get("tamaño_fuente_default", 11)
            c.setFont("Helvetica", tamaño_fuente)
            
            # Procesar cada campo
            for nombre_campo, config_campo in plantilla["campos"].items():
                valor = datos_cheque.get(nombre_campo, "")
                
                if not valor:
                    continue
                
                # Aplicar coordenadas relativas al cheque + offset global
                # X se mantiene igual (desde la izquierda)
                # Y se suma al offset base para que quede en el tope de la hoja
                x = (config_campo["x"] + self.offset_x) * mm
                y = offset_y_base_pts + ((config_campo["y"] + self.offset_y) * mm)
                
                tamaño = config_campo.get("tamaño", tamaño_fuente)
                alineacion = config_campo.get("alineacion", "izquierda")
                
                c.setFont("Helvetica", tamaño)
                
                # Posicionar texto según alineación
                if alineacion == "derecha":
                    c.drawRightString(x, y, str(valor))
                elif alineacion == "centro":
                    c.drawCentredString(x, y, str(valor))
                else:  # izquierda
                    c.drawString(x, y, str(valor))
            
            # Guardar PDF
            c.save()
            return archivo_salida
        
        except (OSError, IOError, PermissionError) as e:
            print(f"ERROR de archivo al generar PDF: {e}")
            return None
        except Exception as e:
            print(f"ERROR inesperado al generar PDF: {e}")
            return None
    
    def _generar_ruta_pdf(self, serie: str, numero: int) -> str:
        """Genera la ruta de salida para el PDF."""
        ahora = datetime.now()
        carpeta = self.ruta_pdfs / f"{ahora.year}{ahora.month:02d}"
        carpeta.mkdir(parents=True, exist_ok=True)
        
        nombre_archivo = f"{serie}_{numero}_{ahora.strftime('%Y%m%d_%H%M%S')}.pdf"
        return str(carpeta / nombre_archivo)
    
    def abrir_vista_previa(self, ruta_pdf: str) -> bool:
        """
        Abre un PDF en el visor predeterminado.
        
        Args:
            ruta_pdf: Ruta del archivo PDF
        
        Returns:
            True si se abrió correctamente, False si falla
        """
        try:
            if not os.path.exists(ruta_pdf):
                print(f"ERROR: Archivo {ruta_pdf} no existe")
                return False
            
            if sys.platform == "win32":
                os.startfile(ruta_pdf)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", ruta_pdf], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", ruta_pdf], check=True)
            
            return True
        
        except (OSError, FileNotFoundError, PermissionError) as e:
            print(f"ERROR de archivo al abrir vista previa: {e}")
            return False
        except Exception as e:
            print(f"ERROR inesperado al abrir vista previa: {e}")
            return False
    
    def listar_impresoras(self) -> list:
        """Lista las impresoras disponibles en el sistema."""
        impresoras = []
        try:
            if sys.platform == "win32":
                import win32print
                for printer in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS):
                    impresoras.append(printer[2])
            else:
                # macOS/Linux usan CUPS
                resultado = subprocess.run(["lpstat", "-a"], capture_output=True, text=True)
                if resultado.returncode == 0:
                    for linea in resultado.stdout.splitlines():
                        if linea:
                            impresoras.append(linea.split()[0])
        except (OSError, subprocess.SubprocessError) as e:
            print(f"Error al listar impresoras: {e}")
            # Fallback a comando PowerShell en Windows si falla win32print
            if sys.platform == "win32":
                try:
                    cmd = 'powershell -Command "Get-Printer | Select-Object -ExpandProperty Name"'
                    resultado = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                    if resultado.returncode == 0:
                        impresoras = [p.strip() for p in resultado.stdout.splitlines() if p.strip()]
                except:
                    pass
        
        return sorted(impresoras) if impresoras else ["Impresora Predeterminada"]

    def imprimir_directamente(self, ruta_pdf: str, nombre_impresora: str = None) -> bool:
        """
        Envía un PDF directamente a la impresora.
        """
        try:
            if not os.path.exists(ruta_pdf):
                print(f"ERROR: Archivo {ruta_pdf} no existe")
                return False
            
            if sys.platform == "win32":
                import win32print
                import win32api
                
                # Si no se especifica impresora, usar la predeterminada
                if not nombre_impresora or nombre_impresora == "Impresora Predeterminada":
                    nombre_impresora = win32print.GetDefaultPrinter()
                
                print(f"Imprimiendo en: {nombre_impresora}")
                
                # MÉTODO NATIVO DE WINDOWS (Sin aplicaciones externas)
                # Usamos win32api para enviar el comando de impresión directamente al driver de la impresora
                try:
                    # Si es la impresora predeterminada, usamos el verbo 'print'
                    if nombre_impresora == win32print.GetDefaultPrinter():
                        win32api.ShellExecute(0, "print", ruta_pdf, None, ".", 0)
                    else:
                        # Si es una impresora específica, usamos 'printto'
                        # Este comando envía el archivo directamente al driver de esa impresora
                        win32api.ShellExecute(0, "printto", ruta_pdf, f'"{nombre_impresora}"', ".", 0)
                    return True
                except (OSError, AttributeError) as e:
                    print(f"Error en impresión nativa: {e}")
                    # Fallback final: abrir el diálogo estándar de Windows
                    os.startfile(ruta_pdf, "print")
                    return True
            
            elif sys.platform == "darwin" or sys.platform.startswith("linux"):
                comando = ["lp"]
                if nombre_impresora and nombre_impresora != "Impresora Predeterminada":
                    comando.extend(["-d", nombre_impresora])
                comando.append(ruta_pdf)
                subprocess.run(comando, check=True)
                return True
        
        except (OSError, subprocess.SubprocessError) as e:
            print(f"ERROR al imprimir: {e}")
            # Fallback final: intentar abrir con el comando print de Windows
            try:
                if sys.platform == "win32":
                    os.startfile(ruta_pdf, "print")
                    return True
            except:
                pass
            return False


if __name__ == "__main__":
    # Test del módulo
    print("Pruebas de impresion.py:")
    print("-" * 80)
    
    # Crear generador
    gen = GeneradorPDF()
    
    # Test 1: Listar plantillas
    print("✓ Test 1: Listando plantillas disponibles...")
    plantillas = gen.listar_plantillas()
    print(f"  Plantillas encontradas: {plantillas}")
    
    # Test 2: Cargar plantilla
    print("✓ Test 2: Cargando plantilla banca_criptoheca...")
    plantilla = gen.cargar_plantilla("banca_criptoheca")
    if plantilla:
        print(f"  Plantilla: {plantilla.get('nombre')}")
        print(f"  Dimensiones: {plantilla.get('ancho_mm')}mm x {plantilla.get('alto_mm')}mm")
        print(f"  Campos: {list(plantilla.get('campos', {}).keys())}")
    
    # Test 3: Generar PDF de prueba
    print("✓ Test 3: Generando PDF de prueba...")
    datos_prueba = {
        "serie": "CD",
        "numero": 1001,
        "fecha": "15/05",
        "beneficiario": "Juan Pérez",
        "importe_num": "125.000",
        "importe_letras": "CIENTO VEINTICINCO MIL GUARANÍES",
        "concepto": "Pago de servicios"
    }
    
    ruta_pdf = gen.generar_pdf(datos_prueba)
    if ruta_pdf:
        print(f"  PDF generado: {ruta_pdf}")
        print(f"  Archivo existe: {os.path.exists(ruta_pdf)}")
    
    print("-" * 80)
    print("✓ Pruebas completadas")
