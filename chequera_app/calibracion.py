"""
Módulo de calibración de impresión.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from config import obtener_config
import os
from datetime import datetime

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
except ImportError:
    print("ERROR: Se requiere reportlab")


class VentanaCalibracion:
    """Ventana modal para calibración de impresión."""
    
    def __init__(self, ventana_padre, generador_pdf, config_path="config.json"):
        """
        Inicializa la ventana de calibración.
        
        Args:
            ventana_padre: Ventana padre para hacerla modal
            generador_pdf: Instancia de GeneradorPDF
            config_path: Ruta del archivo config.json (usará configuración centralizada)
        """
        self.generador_pdf = generador_pdf
        self.config_mgr = obtener_config(config_path, str(Path(__file__).parent))
        self.offset_x_actual = self.config_mgr.offset_x
        self.offset_y_actual = self.config_mgr.offset_y
        
        # Crear ventana modal
        self.ventana = tk.Toplevel(ventana_padre)
        self.ventana.title("Calibración de Impresión")
        self.ventana.geometry("600x500")
        self.ventana.resizable(False, False)
        
        # Hacer modal
        self.ventana.grab_set()
        self.ventana.transient(ventana_padre)
        
        # Crear interfaz
        self._crear_interfaz()
        
        # Posicionar en centro de la pantalla
        self.ventana.update_idletasks()
        x = ventana_padre.winfo_x() + (ventana_padre.winfo_width() // 2) - (self.ventana.winfo_width() // 2)
        y = ventana_padre.winfo_y() + (ventana_padre.winfo_height() // 2) - (self.ventana.winfo_height() // 2)
        self.ventana.geometry(f"+{x}+{y}")
    
    def _guardar_config(self):
        """Guarda la configuración usando el gestor centralizado."""
        self.config_mgr.offset_x = self.offset_x_actual
        self.config_mgr.offset_y = self.offset_y_actual
        return self.config_mgr.guardar()
    
    def _crear_interfaz(self):
        """Crea la interfaz de calibración."""
        
        # Título
        frame_titulo = ttk.Frame(self.ventana)
        frame_titulo.pack(fill=tk.X, padx=15, pady=15)
        
        titulo = ttk.Label(frame_titulo, text="Calibración de Impresión", 
                          font=("Arial", 12, "bold"))
        titulo.pack(anchor=tk.W)
        
        info = ttk.Label(frame_titulo, text="Ajusta los offset para alinear correctamente los campos en el papel preimpreso",
                        font=("Arial", 9), foreground="gray")
        info.pack(anchor=tk.W)
        
        # Frame de controles
        frame_controles = ttk.LabelFrame(self.ventana, text="Ajustes de Offset (mm)", padding=15)
        frame_controles.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Offset X
        ttk.Label(frame_controles, text="Offset X (horizontal):", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        frame_x = ttk.Frame(frame_controles)
        frame_x.grid(row=0, column=1, sticky=tk.EW, pady=10, padx=10)
        
        btn_x_menos = ttk.Button(frame_x, text="← Izquierda", width=12, command=self._offset_x_menos)
        btn_x_menos.pack(side=tk.LEFT, padx=5)
        
        self.entry_x = ttk.Entry(frame_x, width=8, font=("Arial", 11, "bold"), justify=tk.CENTER)
        self.entry_x.pack(side=tk.LEFT, padx=5)
        self.entry_x.bind("<Return>", self._actualizar_desde_entry)
        
        btn_x_mas = ttk.Button(frame_x, text="Derecha →", width=12, command=self._offset_x_mas)
        btn_x_mas.pack(side=tk.LEFT, padx=5)
        
        # Offset Y
        ttk.Label(frame_controles, text="Offset Y (vertical):", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        frame_y = ttk.Frame(frame_controles)
        frame_y.grid(row=1, column=1, sticky=tk.EW, pady=10, padx=10)
        
        btn_y_menos = ttk.Button(frame_y, text="↑ Arriba", width=12, command=self._offset_y_menos)
        btn_y_menos.pack(side=tk.LEFT, padx=5)
        
        self.entry_y = ttk.Entry(frame_y, width=8, font=("Arial", 11, "bold"), justify=tk.CENTER)
        self.entry_y.pack(side=tk.LEFT, padx=5)
        self.entry_y.bind("<Return>", self._actualizar_desde_entry)
        
        btn_y_mas = ttk.Button(frame_y, text="Abajo ↓", width=12, command=self._offset_y_mas)
        btn_y_mas.pack(side=tk.LEFT, padx=5)
        
        # Tamaño de paso
        ttk.Label(frame_controles, text="Paso (mm):", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        self.spinbox_paso = ttk.Spinbox(frame_controles, from_=0.1, to=5, width=8, font=("Arial", 10), justify=tk.CENTER)
        self.spinbox_paso.set(0.5)
        self.spinbox_paso.grid(row=2, column=1, sticky=tk.W, padx=10, pady=10)
        
        # Valores actuales
        frame_valores = ttk.LabelFrame(self.ventana, text="Valores Actuales", padding=10)
        frame_valores.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(frame_valores, text="X:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(frame_valores, text="Y:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.lbl_x_valor = ttk.Label(frame_valores, text="", font=("Arial", 10), foreground="blue")
        self.lbl_x_valor.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.lbl_y_valor = ttk.Label(frame_valores, text="", font=("Arial", 10), foreground="blue")
        self.lbl_y_valor.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Botones de acción
        frame_botones = ttk.Frame(self.ventana)
        frame_botones.pack(fill=tk.X, padx=15, pady=15)
        
        btn_prueba = ttk.Button(frame_botones, text="Generar PDF de Prueba", command=self._generar_pdf_prueba)
        btn_prueba.pack(side=tk.LEFT, padx=5)
        
        btn_resetear = ttk.Button(frame_botones, text="Resetear a 0", command=self._resetear_offset)
        btn_resetear.pack(side=tk.LEFT, padx=5)
        
        btn_guardar = ttk.Button(frame_botones, text="Guardar Calibración", command=self._guardar_calibracion)
        btn_guardar.pack(side=tk.RIGHT, padx=5)
        
        btn_cerrar = ttk.Button(frame_botones, text="Cerrar", command=self.ventana.destroy)
        btn_cerrar.pack(side=tk.RIGHT, padx=5)
        
        # Actualizar displays
        self._actualizar_display()
    
    def _actualizar_display(self):
        """Actualiza los displays de valores."""
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, f"{self.offset_x_actual:.1f}")
        
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, f"{self.offset_y_actual:.1f}")
        
        self.lbl_x_valor.config(text=f"{self.offset_x_actual:.2f} mm")
        self.lbl_y_valor.config(text=f"{self.offset_y_actual:.2f} mm")
    
    def _obtener_paso(self):
        """Obtiene el valor de paso."""
        try:
            return float(self.spinbox_paso.get())
        except:
            return 0.5
    
    def _offset_x_mas(self):
        """Incrementa offset X."""
        self.offset_x_actual += self._obtener_paso()
        self._actualizar_display()
    
    def _offset_x_menos(self):
        """Decrementa offset X."""
        self.offset_x_actual -= self._obtener_paso()
        self._actualizar_display()
    
    def _offset_y_mas(self):
        """Incrementa offset Y."""
        self.offset_y_actual += self._obtener_paso()
        self._actualizar_display()
    
    def _offset_y_menos(self):
        """Decrementa offset Y."""
        self.offset_y_actual -= self._obtener_paso()
        self._actualizar_display()
    
    def _actualizar_desde_entry(self, event=None):
        """Actualiza offset desde los entry fields."""
        try:
            self.offset_x_actual = float(self.entry_x.get())
            self.offset_y_actual = float(self.entry_y.get())
            self._actualizar_display()
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numéricos válidos")
            self._actualizar_display()
    
    def _generar_pdf_prueba(self):
        """Genera un PDF de prueba con líneas de referencia."""
        try:
            # Crear PDF con líneas de guía
            ruta_pdf = self._crear_pdf_calibracion()
            
            if ruta_pdf:
                # Abrir vista previa
                self.generador_pdf.abrir_vista_previa(ruta_pdf)
                messagebox.showinfo("Éxito", f"PDF de prueba generado:\n{ruta_pdf}\n\n"
                                           "Compara con el papel preimpreso e imprime directamente.")
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF de prueba")
        except (OSError, IOError, PermissionError) as e:
            messagebox.showerror("Error", f"Error de archivo al generar PDF: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado al generar PDF: {e}")
    
    def _crear_pdf_calibracion(self):
        """Crea un PDF con líneas de calibración."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            
            # Crear carpeta si no existe
            carpeta = Path(self.generador_pdf.ruta_pdfs)
            carpeta.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre del archivo
            ahora = datetime.now()
            ruta_pdf = str(carpeta / f"calibracion_{ahora.strftime('%Y%m%d_%H%M%S')}.pdf")
            
            # Crear canvas
            c = canvas.Canvas(ruta_pdf, pagesize=(210*mm, 99*mm))
            
            # Aplicar offset
            offset_x = self.offset_x_actual
            offset_y = self.offset_y_actual
            
            # Dibujar líneas de referencia
            c.setStrokeColor(0.7, 0.7, 0.7)  # Gris
            c.setLineWidth(0.5)
            
            # Líneas verticales cada 10mm
            for x in range(0, 210, 10):
                x_pos = (x + offset_x) * mm
                c.line(x_pos, 0, x_pos, 99*mm)
                c.setFont("Helvetica", 6)
                c.drawString(x_pos + 1*mm, 2*mm, f"{x}")
            
            # Líneas horizontales cada 10mm
            for y in range(0, 99, 10):
                y_pos = (y + offset_y) * mm
                c.line(0, y_pos, 210*mm, y_pos)
                c.setFont("Helvetica", 6)
                c.drawString(2*mm, y_pos + 1*mm, f"{y}")
            
            # Dibujar cruz en el centro
            center_x = (105 + offset_x) * mm
            center_y = (49.5 + offset_y) * mm
            c.setStrokeColor(1, 0, 0)  # Rojo
            c.setLineWidth(1)
            c.line(center_x - 5*mm, center_y, center_x + 5*mm, center_y)
            c.line(center_x, center_y - 5*mm, center_x, center_y + 5*mm)
            
            # Información
            c.setFont("Helvetica", 8)
            c.setFillColor(0, 0, 0)
            c.drawString(5*mm, 95*mm, f"Offset X: {offset_x:.2f}mm | Offset Y: {offset_y:.2f}mm")
            c.drawString(5*mm, 90*mm, "Imprime y compara con el papel preimpreso")
            
            c.save()
            return ruta_pdf
        except (OSError, IOError, PermissionError) as e:
            print(f"Error de archivo al crear PDF de calibración: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al crear PDF de calibración: {e}")
            return None
    
    def _resetear_offset(self):
        """Resetea los offset a 0."""
        if messagebox.askyesno("Confirmar", "¿Resetear offset a 0?"):
            self.offset_x_actual = 0
            self.offset_y_actual = 0
            self._actualizar_display()
    
    def _guardar_calibracion(self):
        """Guarda la calibración en config.json."""
        # Actualizar valores desde entries por si fueron editados
        try:
            self.offset_x_actual = float(self.entry_x.get())
            self.offset_y_actual = float(self.entry_y.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numéricos válidos")
            return
        
        if self._guardar_config():
            # Actualizar generador PDF
            self.generador_pdf.offset_x = self.offset_x_actual
            self.generador_pdf.offset_y = self.offset_y_actual
            
            messagebox.showinfo("Éxito", "Calibración guardada en config.json\n\n"
                                        f"Offset X: {self.offset_x_actual:.2f}mm\n"
                                        f"Offset Y: {self.offset_y_actual:.2f}mm")
            self.ventana.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar la calibración")


if __name__ == "__main__":
    # Demo de prueba
    print("Este módulo se usa desde main.py")
