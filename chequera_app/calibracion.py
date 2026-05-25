"""
Modulo de calibracion de impresion.
Proporciona una interfaz grafica intuitiva para ajustar offsets de impresion.
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
    """Ventana modal para calibracion de impresion con interfaz intuitiva."""

    COLORES = {
        "fondo": "#f5f5f5",
        "x": "#1a73e8",
        "y": "#e8711a",
        "exito": "#1b8a3d",
        "error": "#d93025",
        "texto_secundario": "#5f6368",
    }

    def __init__(self, ventana_padre, generador_pdf, config_path="config.json"):
        self.generador_pdf = generador_pdf
        self.config_mgr = obtener_config(config_path, str(Path(__file__).parent))
        self.offset_x_actual = self.config_mgr.offset_x
        self.offset_y_actual = self.config_mgr.offset_y
        self._paso = 0.5

        self.ventana = tk.Toplevel(ventana_padre)
        self.ventana.title("Calibracion de Impresion")
        self.ventana.geometry("680x620")
        self.ventana.resizable(False, False)
        self.ventana.configure(bg=self.COLORES["fondo"])

        self.ventana.grab_set()
        self.ventana.transient(ventana_padre)

        self._crear_interfaz()

        self.ventana.update_idletasks()
        x = ventana_padre.winfo_x() + (ventana_padre.winfo_width() // 2) - (self.ventana.winfo_width() // 2)
        y = ventana_padre.winfo_y() + (ventana_padre.winfo_height() // 2) - (self.ventana.winfo_height() // 2)
        self.ventana.geometry(f"+{x}+{y}")

    def _guardar_config(self):
        self.config_mgr.offset_x = self.offset_x_actual
        self.config_mgr.offset_y = self.offset_y_actual
        return self.config_mgr.guardar()

    def _crear_interfaz(self):
        self._crear_encabezado()
        self._crear_diagrama()
        self._crear_controles()
        self._crear_barra_estado()
        self._crear_acciones()
        self._actualizar_display()

    def _crear_encabezado(self):
        frame = tk.Frame(self.ventana, bg=self.COLORES["fondo"])
        frame.pack(fill=tk.X, padx=20, pady=(15, 5))

        tk.Label(frame, text="Calibracion de Impresion",
                 font=("Segoe UI", 14, "bold"), bg=self.COLORES["fondo"],
                 fg="#202124").pack(anchor=tk.W)

        tk.Label(frame, text="Ajusta la posicion de los campos en el papel preimpreso del cheque",
                 font=("Segoe UI", 9), bg=self.COLORES["fondo"],
                 fg=self.COLORES["texto_secundario"]).pack(anchor=tk.W, pady=(2, 0))

        separator = ttk.Separator(self.ventana, orient="horizontal")
        separator.pack(fill=tk.X, padx=20, pady=(10, 5))

    def _crear_diagrama(self):
        frame = tk.Frame(self.ventana, bg=self.COLORES["fondo"])
        frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        canvas_diag = tk.Canvas(frame, width=640, height=70,
                                bg="#ffffff", highlightthickness=1,
                                highlightbackground="#dadce0")
        canvas_diag.pack()

        center_x, center_y = 320, 35

        canvas_diag.create_text(center_x, 10, text="PAPEL PREIMPRESO",
                                font=("Segoe UI", 7), fill=self.COLORES["texto_secundario"])

        canvas_diag.create_rectangle(center_x - 100, center_y - 15,
                                     center_x + 100, center_y + 15,
                                     outline=self.COLORES["x"], width=2, dash=(4, 2))
        canvas_diag.create_text(center_x, center_y - 5, text="Contenido del cheque",
                                font=("Segoe UI", 8), fill=self.COLORES["x"])

        canvas_diag.create_line(center_x - 130, center_y,
                                 center_x - 105, center_y,
                                 arrow=tk.LAST, fill=self.COLORES["x"], width=2)
        canvas_diag.create_text(center_x - 118, center_y - 12, text="X",
                                font=("Segoe UI", 8, "bold"), fill=self.COLORES["x"])

        canvas_diag.create_line(center_x + 105, center_y,
                                 center_x + 140, center_y,
                                 arrow=tk.LAST, fill=self.COLORES["x"], width=2)
        canvas_diag.create_text(center_x + 128, center_y - 12, text="X+",
                                font=("Segoe UI", 8, "bold"), fill=self.COLORES["x"])

        canvas_diag.create_line(center_x, center_y - 20,
                                 center_x, center_y - 18,
                                 arrow=tk.LAST, fill=self.COLORES["y"], width=2)
        canvas_diag.create_text(center_x + 15, center_y - 28, text="Y-",
                                font=("Segoe UI", 8, "bold"), fill=self.COLORES["y"])

        canvas_diag.create_line(center_x, center_y + 20,
                                 center_x, center_y + 18,
                                 arrow=tk.LAST, fill=self.COLORES["y"], width=2)
        canvas_diag.create_text(center_x + 15, center_y + 22, text="Y+",
                                font=("Segoe UI", 8, "bold"), fill=self.COLORES["y"])

        tk.Label(frame,
                 text="X+ = mueve a la derecha  |  Y+ = mueve hacia abajo  |  Usa valores negativos para la direccion opuesta",
                 font=("Segoe UI", 7), bg=self.COLORES["fondo"],
                 fg=self.COLORES["texto_secundario"]).pack(pady=(3, 0))

    def _crear_controles(self):
        container = tk.Frame(self.ventana, bg=self.COLORES["fondo"])
        container.pack(fill=tk.BOTH, expand=True, padx=20)

        self._crear_eje_x(container)
        self._crear_eje_y(container)
        self._crear_selector_paso(container)

    def _crear_eje_x(self, parent):
        frame = tk.LabelFrame(parent, text=" Ajuste Horizontal (X) ",
                              font=("Segoe UI", 10, "bold"),
                              fg=self.COLORES["x"], bg=self.COLORES["fondo"],
                              padx=10, pady=10)
        frame.pack(fill=tk.X, pady=(0, 8))

        inner = tk.Frame(frame, bg=self.COLORES["fondo"])
        inner.pack()

        btn_left = tk.Button(inner, text="\u25C0  Izquierda",
                             font=("Segoe UI", 9, "bold"),
                             bg="#e8f0fe", fg=self.COLORES["x"],
                             activebackground="#d2e3fc",
                             relief=tk.RAISED, bd=1, padx=8, pady=4,
                             command=self._offset_x_menos)
        btn_left.pack(side=tk.LEFT, padx=3)

        self.entry_x = tk.Entry(inner, width=7, font=("Segoe UI", 14, "bold"),
                                justify=tk.CENTER, bd=1, relief=tk.SOLID,
                                fg=self.COLORES["x"])
        self.entry_x.pack(side=tk.LEFT, padx=8)
        self.entry_x.bind("<Return>", self._actualizar_desde_entry)
        self.entry_x.bind("<MouseWheel>", lambda e: self._offset_x_mas() if e.delta > 0 else self._offset_x_menos())

        btn_right = tk.Button(inner, text="Derecha  \u25B6",
                              font=("Segoe UI", 9, "bold"),
                              bg="#e8f0fe", fg=self.COLORES["x"],
                              activebackground="#d2e3fc",
                              relief=tk.RAISED, bd=1, padx=8, pady=4,
                              command=self._offset_x_mas)
        btn_right.pack(side=tk.LEFT, padx=3)

        tk.Label(inner, text="mm", font=("Segoe UI", 10),
                 bg=self.COLORES["fondo"],
                 fg=self.COLORES["texto_secundario"]).pack(side=tk.LEFT, padx=(2, 0))

    def _crear_eje_y(self, parent):
        frame = tk.LabelFrame(parent, text=" Ajuste Vertical (Y) ",
                              font=("Segoe UI", 10, "bold"),
                              fg=self.COLORES["y"], bg=self.COLORES["fondo"],
                              padx=10, pady=10)
        frame.pack(fill=tk.X, pady=(0, 8))

        inner = tk.Frame(frame, bg=self.COLORES["fondo"])
        inner.pack()

        btn_up = tk.Button(inner, text="\u25B2  Arriba",
                           font=("Segoe UI", 9, "bold"),
                           bg="#fef3e8", fg=self.COLORES["y"],
                           activebackground="#fde8d2",
                           relief=tk.RAISED, bd=1, padx=8, pady=4,
                           command=self._offset_y_menos)
        btn_up.pack(side=tk.LEFT, padx=3)

        self.entry_y = tk.Entry(inner, width=7, font=("Segoe UI", 14, "bold"),
                                justify=tk.CENTER, bd=1, relief=tk.SOLID,
                                fg=self.COLORES["y"])
        self.entry_y.pack(side=tk.LEFT, padx=8)
        self.entry_y.bind("<Return>", self._actualizar_desde_entry)
        self.entry_y.bind("<MouseWheel>", lambda e: self._offset_y_mas() if e.delta > 0 else self._offset_y_menos())

        btn_down = tk.Button(inner, text="Abajo  \u25BC",
                             font=("Segoe UI", 9, "bold"),
                             bg="#fef3e8", fg=self.COLORES["y"],
                             activebackground="#fde8d2",
                             relief=tk.RAISED, bd=1, padx=8, pady=4,
                             command=self._offset_y_mas)
        btn_down.pack(side=tk.LEFT, padx=3)

        tk.Label(inner, text="mm", font=("Segoe UI", 10),
                 bg=self.COLORES["fondo"],
                 fg=self.COLORES["texto_secundario"]).pack(side=tk.LEFT, padx=(2, 0))

    def _crear_selector_paso(self, parent):
        frame = tk.LabelFrame(parent, text=" Precision del Ajuste ",
                              font=("Segoe UI", 10, "bold"),
                              bg=self.COLORES["fondo"], padx=10, pady=8)
        frame.pack(fill=tk.X, pady=(0, 5))

        inner = tk.Frame(frame, bg=self.COLORES["fondo"])
        inner.pack()

        presets = [("Fino", 0.1), ("Medio", 0.5), ("Grueso", 1.0), ("Grande", 2.0)]

        def seleccionar_paso(valor):
            self._paso = valor
            self.lbl_paso_valor.config(text=f"{valor:.1f} mm")
            for b in grupo_paso:
                if abs(b.valor - valor) < 0.01:
                    b.config(bg="#dadce0")
                else:
                    b.config(bg="#f1f3f4")

        grupo_paso = []
        for texto, valor in presets:
            btn = tk.Button(inner, text=texto, font=("Segoe UI", 8),
                            bg="#f1f3f4", relief=tk.RAISED, bd=1,
                            padx=10, pady=2, width=7,
                            command=lambda v=valor: seleccionar_paso(v))
            btn.valor = valor
            btn.pack(side=tk.LEFT, padx=3)
            grupo_paso.append(btn)


        tk.Label(inner, text="Paso actual:", font=("Segoe UI", 8),
                 bg=self.COLORES["fondo"],
                 fg=self.COLORES["texto_secundario"]).pack(side=tk.LEFT, padx=(15, 3))
        self.lbl_paso_valor = tk.Label(inner, text="", font=("Segoe UI", 9, "bold"),
                                       bg=self.COLORES["fondo"], fg="#202124")
        self.lbl_paso_valor.pack(side=tk.LEFT)

        seleccionar_paso(self._paso)

    def _crear_barra_estado(self):
        container = tk.Frame(self.ventana, bg=self.COLORES["fondo"])
        container.pack(fill=tk.X, padx=20, pady=(0, 10))

        frame = tk.LabelFrame(container, text=" Estado Actual ",
                              font=("Segoe UI", 9, "bold"),
                              bg=self.COLORES["fondo"], padx=10, pady=8)
        frame.pack(fill=tk.X)

        grid = tk.Frame(frame, bg=self.COLORES["fondo"])
        grid.pack()

        tk.Label(grid, text="Offset X:", font=("Segoe UI", 9, "bold"),
                 bg=self.COLORES["fondo"], fg=self.COLORES["x"]).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.lbl_x_valor = tk.Label(grid, text="", font=("Segoe UI", 11, "bold"),
                                    bg="#e8f0fe", fg=self.COLORES["x"],
                                    padx=10, pady=2)
        self.lbl_x_valor.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))

        tk.Label(grid, text="Offset Y:", font=("Segoe UI", 9, "bold"),
                 bg=self.COLORES["fondo"], fg=self.COLORES["y"]).grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.lbl_y_valor = tk.Label(grid, text="", font=("Segoe UI", 11, "bold"),
                                    bg="#fef3e8", fg=self.COLORES["y"],
                                    padx=10, pady=2)
        self.lbl_y_valor.grid(row=0, column=3, sticky=tk.W)

        tk.Label(grid, text="(= sin ajuste)", font=("Segoe UI", 8),
                 bg=self.COLORES["fondo"],
                 fg=self.COLORES["texto_secundario"]).grid(row=0, column=4, sticky=tk.W, padx=(10, 0))

    def _crear_acciones(self):
        separator = ttk.Separator(self.ventana, orient="horizontal")
        separator.pack(fill=tk.X, padx=20)

        frame = tk.Frame(self.ventana, bg=self.COLORES["fondo"])
        frame.pack(fill=tk.X, padx=20, pady=12)

        btn_prueba = tk.Button(frame, text="Generar PDF de Prueba",
                               font=("Segoe UI", 10, "bold"),
                               bg="#1a73e8", fg="white",
                               activebackground="#1557b0",
                               relief=tk.RAISED, bd=1, padx=15, pady=6,
                               command=self._generar_pdf_prueba)
        btn_prueba.pack(side=tk.LEFT, padx=3)

        btn_resetear = tk.Button(frame, text="Resetear a 0",
                                 font=("Segoe UI", 10),
                                 bg="#f1f3f4", fg="#5f6368",
                                 activebackground="#dadce0",
                                 relief=tk.RAISED, bd=1, padx=15, pady=6,
                                 command=self._resetear_offset)
        btn_resetear.pack(side=tk.LEFT, padx=3)

        btn_cerrar = tk.Button(frame, text="Cerrar",
                               font=("Segoe UI", 10),
                               bg="#f1f3f4", fg="#5f6368",
                               activebackground="#dadce0",
                               relief=tk.RAISED, bd=1, padx=15, pady=6,
                               command=self.ventana.destroy)
        btn_cerrar.pack(side=tk.RIGHT, padx=3)

        btn_guardar = tk.Button(frame, text="Guardar Calibracion",
                                font=("Segoe UI", 10, "bold"),
                                bg="#1b8a3d", fg="white",
                                activebackground="#157a34",
                                relief=tk.RAISED, bd=1, padx=15, pady=6,
                                command=self._guardar_calibracion)
        btn_guardar.pack(side=tk.RIGHT, padx=3)

    def _actualizar_display(self):
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, f"{self.offset_x_actual:.1f}")

        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, f"{self.offset_y_actual:.1f}")

        self.lbl_x_valor.config(text=f"{self.offset_x_actual:+.2f} mm")
        self.lbl_y_valor.config(text=f"{self.offset_y_actual:+.2f} mm")

    def _obtener_paso(self):
        return self._paso

    def _offset_x_mas(self):
        self.offset_x_actual += self._obtener_paso()
        self._actualizar_display()

    def _offset_x_menos(self):
        self.offset_x_actual -= self._obtener_paso()
        self._actualizar_display()

    def _offset_y_mas(self):
        self.offset_y_actual += self._obtener_paso()
        self._actualizar_display()

    def _offset_y_menos(self):
        self.offset_y_actual -= self._obtener_paso()
        self._actualizar_display()

    def _actualizar_desde_entry(self, event=None):
        try:
            self.offset_x_actual = float(self.entry_x.get())
            self.offset_y_actual = float(self.entry_y.get())
            self._actualizar_display()
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numericos validos")
            self._actualizar_display()

    def _generar_pdf_prueba(self):
        try:
            ruta_pdf = self._crear_pdf_calibracion()

            if ruta_pdf:
                self.generador_pdf.abrir_vista_previa(ruta_pdf)
                messagebox.showinfo(
                    "PDF Generado",
                    "PDF de prueba generado correctamente.\n\n"
                    "1. Imprime este PDF en el papel preimpreso del cheque\n"
                    "2. Compara las lineas con los bordes del papel\n"
                    "3. Ajusta los offset X y Y para alinear las lineas\n"
                    "4. Genera otro PDF de prueba para verificar\n"
                    "5. Cuando este alineado, haz clic en Guardar Calibracion"
                )
            else:
                messagebox.showerror("Error", "No se pudo generar el PDF de prueba")
        except (OSError, IOError, PermissionError) as e:
            messagebox.showerror("Error", f"Error de archivo al generar PDF: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado al generar PDF: {e}")

    def _crear_pdf_calibracion(self):
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from reportlab.lib.pagesizes import A4, landscape

            carpeta = Path(self.generador_pdf.ruta_pdfs)
            carpeta.mkdir(parents=True, exist_ok=True)

            ahora = datetime.now()
            ruta_pdf = str(carpeta / f"calibracion_{ahora.strftime('%Y%m%d_%H%M%S')}.pdf")

            ancho_pagina, alto_pagina = landscape(A4)

            ancho_cheque_mm = 175
            alto_cheque_mm = 76
            c = canvas.Canvas(ruta_pdf, pagesize=landscape(A4))

            offset_y_base = alto_pagina - (alto_cheque_mm * mm)

            offset_x = self.offset_x_actual
            offset_y = self.offset_y_actual

            c.setStrokeColor(0.7, 0.7, 0.7)
            c.setLineWidth(0.5)

            for x in range(0, ancho_cheque_mm + 1, 10):
                x_pos = (x + offset_x) * mm
                c.line(x_pos, offset_y_base, x_pos, offset_y_base + alto_cheque_mm * mm)
                c.setFont("Helvetica", 5)
                c.drawString(x_pos + 0.5 * mm, offset_y_base + 1 * mm, f"{x}")

            for y in range(0, alto_cheque_mm + 1, 10):
                y_pos = offset_y_base + (y + offset_y) * mm
                c.line(0, y_pos, ancho_cheque_mm * mm, y_pos)
                c.setFont("Helvetica", 5)
                c.drawString(1 * mm, y_pos + 0.5 * mm, f"{y}")

            center_x = (ancho_cheque_mm / 2 + offset_x) * mm
            center_y = offset_y_base + (alto_cheque_mm / 2 + offset_y) * mm
            c.setStrokeColor(1, 0, 0)
            c.setLineWidth(1.5)
            c.line(center_x - 5 * mm, center_y, center_x + 5 * mm, center_y)
            c.line(center_x, center_y - 5 * mm, center_x, center_y + 5 * mm)

            c.setFont("Helvetica", 7)
            c.setFillColor(0, 0, 0)
            c.drawString(2 * mm, offset_y_base + alto_cheque_mm * mm - 8 * mm,
                         f"Offset X: {offset_x:+.2f}mm  |  Offset Y: {offset_y:+.2f}mm")
            c.drawString(2 * mm, offset_y_base + alto_cheque_mm * mm - 12 * mm,
                         "Ajusta los offset hasta que las lineas coincidan con el papel preimpreso")

            c.save()
            return ruta_pdf
        except (OSError, IOError, PermissionError) as e:
            print(f"Error de archivo al crear PDF de calibracion: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al crear PDF de calibracion: {e}")
            return None

    def _resetear_offset(self):
        if messagebox.askyesno("Confirmar", "Resetear ambos offset a 0.00?"):
            self.offset_x_actual = 0
            self.offset_y_actual = 0
            self._actualizar_display()

    def _guardar_calibracion(self):
        try:
            self.offset_x_actual = float(self.entry_x.get())
            self.offset_y_actual = float(self.entry_y.get())
        except ValueError:
            messagebox.showerror("Error", "Ingresa valores numericos validos")
            return

        if self._guardar_config():
            self.generador_pdf.offset_x = self.offset_x_actual
            self.generador_pdf.offset_y = self.offset_y_actual

            messagebox.showinfo(
                "Calibracion Guardada",
                f"Offset X: {self.offset_x_actual:+.2f} mm\n"
                f"Offset Y: {self.offset_y_actual:+.2f} mm\n\n"
                "Los nuevos valores se aplicaran a partir del proximo cheque."
            )
            self.ventana.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar la calibracion. Verifica permisos del archivo config.json.")


if __name__ == "__main__":
    print("Este modulo se usa desde main.py")
