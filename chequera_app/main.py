"""
Aplicación principal del sistema de cheques.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import date
import csv
import sys
import os
from config import obtener_config
from backup import GestorBackup

from db import GestionadorCheques
from impresion import GeneradorPDF
from num2letras import numero_a_letras
from calibracion import VentanaCalibracion
from carga_masiva import VentanaCargaMasiva

# Intentar importar tkcalendar para date picker
try:
    from tkcalendar import DateEntry
    TIENE_TKCALENDAR = True
except ImportError:
    TIENE_TKCALENDAR = False
    print("Advertencia: tkcalendar no instalado. Se usará selector de fecha manual.")


class CamposTracker:
    """Rastrea cambios en el formulario para detectar datos sin guardar."""

    def __init__(self, app):
        self.app = app
        self._valores_iniciales = {}

    def guardar_snapshot(self):
        vals = {}
        vals["serie"] = app_getattr(self.app, "entry_serie", "get", "")
        vals["numero"] = app_getattr(self.app, "entry_numero", "get", "")
        vals["beneficiario"] = app_getattr(self.app, "entry_beneficiario", "get", "")
        vals["importe"] = app_getattr(self.app, "entry_importe", "get", "")
        self._valores_iniciales = vals

    def hay_cambios(self):
        if not self._valores_iniciales:
            return False
        return (
            app_getattr(self.app, "entry_serie", "get", "") != self._valores_iniciales.get("serie")
            or app_getattr(self.app, "entry_numero", "get", "") != self._valores_iniciales.get("numero")
            or app_getattr(self.app, "entry_beneficiario", "get", "") != self._valores_iniciales.get("beneficiario")
            or app_getattr(self.app, "entry_importe", "get", "") != self._valores_iniciales.get("importe")
        )


def app_getattr(obj, attr, method, default=""):
    sub = getattr(obj, attr, None)
    if sub is None:
        return default
    met = getattr(sub, method, None)
    if met is None:
        return default
    try:
        return met()
    except Exception:
        return default


class AplicacionCheques:
    """Aplicación principal de gestión de cheques."""
    
    COLORES = {
        "bg": "#f4f6f8",
        "surface": "#ffffff",
        "primary": "#1565c0",
        "primary_dark": "#0d47a1",
        "secondary": "#546e7a",
        "border": "#cfd8dc",
        "success": "#2e7d32",
        "error": "#c62828",
        "warning": "#ef6c00",
    }
    
    def __init__(self, ventana_principal):
        """Inicializa la aplicación."""
        self.ventana = ventana_principal
        self.ventana.title("Sistema de Emisión de Cheques")
        self.ventana.geometry("1000x700")
        self.ventana.minsize(800, 550)
        
        dir_base = Path(__file__).parent
        self.config_mgr = obtener_config(str(dir_base / "config.json"), str(dir_base))
        ruta_bd = self.config_mgr.ruta_bd
        self.db = GestionadorCheques(str(ruta_bd))
        self.generador_pdf = GeneradorPDF()
        
        self._aplicar_estilos()
        
        # Estado del formulario
        self._formulario_sucio = False
        self.datos_actuales = {}
        self.var_importe = tk.StringVar()
        self.var_importe.trace_add("write", self._on_importe_change)
        
        self.vcmd_numerico = (self.ventana.register(self._validar_input_numerico), '%P', '%W')
        
        # Contenedor principal
        self._crear_menu()
        self._crear_banner()
        self._crear_statusbar()
        self._crear_notebook()
        
        tracker = CamposTracker(self)
        self._tracker = tracker
        
        self.ventana.protocol("WM_DELETE_WINDOW", self._confirmar_salir)

    def _actualizar_statusbar(self):
        n = len(self.tree_historial.get_children())
        plantilla = self.combo_plantilla.get() if hasattr(self, "combo_plantilla") else "-"
        impresora = self.combo_impresora.get() if hasattr(self, "combo_impresora") else "-"
        self._status_izq.config(text=f"{plantilla}  |  {impresora}")
        self._status_der.config(text=f"{n} cheque{'s' if n != 1 else ''}")

    def _validar_input_numerico(self, nuevo_valor, widget_name):
        """Permite solo la entrada de dígitos y limita la longitud."""
        # Limpiar de puntos para validar la longitud real de los dígitos
        solo_numeros = "".join(filter(str.isdigit, nuevo_valor))
        
        # Si está vacío es válido (borrado total)
        if not nuevo_valor:
            return True
            
        # Validar que sean solo dígitos (y puntos que nosotros ponemos)
        for char in nuevo_valor:
            if not char.isdigit() and char != '.':
                return False

        # Límites de longitud (dígitos puros)
        if "importe" in widget_name.lower():
            return len(solo_numeros) <= 10 # Hasta 9.999.999.999 (10 dígitos)
        else:
            return len(solo_numeros) <= 12 # Otros campos como Número
            
        return True
    
    def _sanitizar_string(self, texto: str, max_longitud: int = None, permitir_caracteres_especiales: bool = False) -> str:
        """
        Sanitiza un string de texto para prevenir inyección de caracteres peligrosos.
        
        Args:
            texto: Texto a sanitizar
            max_longitud: Longitud máxima permitida (None = sin límite)
            permitir_caracteres_especiales: Si True, permite más caracteres especiales
        
        Returns:
            Texto sanitizado
        """
        if not texto:
            return ""
        
        # Eliminar espacios en blanco al inicio y final
        texto = texto.strip()
        
        # Convertir a mayúsculas para campos específicos
        texto = texto.upper()
        
        caracteres_permitidos = "ABCDEFGHIJKLMNOPQRSTUVWXYZÑÁÉÍÓÚáéíóú0123456789 .,;-/"
        
        if permitir_caracteres_especiales:
            # Permitir más caracteres para campos como concepto
            caracteres_permitidos += ":'\"()áéíóúÁÉÍÓÚ"
        
        # Filtrar caracteres no permitidos
        texto_sanitizado = ""
        for char in texto:
            if char in caracteres_permitidos:
                texto_sanitizado += char
        
        # Aplicar límite de longitud
        if max_longitud:
            texto_sanitizado = texto_sanitizado[:max_longitud]
        
        return texto_sanitizado

    def _aplicar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        C = self.COLORES
        self.ventana.configure(bg=C["bg"])

        style.configure("TNotebook", background=C["bg"], borderwidth=0, padding=0)
        style.configure("TNotebook.Tab",
            padding=[30, 10],
            font=("Segoe UI", 10, "bold"),
            background="#e0e0e0",
            foreground=C["secondary"],
            borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", C["primary"]), ("active", "#e3f2fd")],
            foreground=[("selected", "white"), ("active", C["primary"])],
            font=[("selected", ("Segoe UI", 11, "bold")), ("!selected", ("Segoe UI", 10, "bold"))])

        style.configure("TLabel", background=C["bg"], font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=C["primary"])
        style.configure("TButton", padding=8, font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", background=C["primary"], foreground="white")
        style.map("Primary.TButton", background=[("active", C["primary_dark"])])
        style.configure("TLabelframe", background=C["bg"], bordercolor=C["border"], borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=C["bg"], font=("Segoe UI", 10, "bold"), foreground=C["secondary"])

        style.configure("Status.TLabel", background="#263238", foreground="#eceff1",
                        font=("Segoe UI", 9), padding=(10, 3))
        style.configure("Banner.TLabel", background=C["primary_dark"], foreground="white",
                        font=("Segoe UI", 14, "bold"), padding=(15, 8))
        style.configure("BannerSub.TLabel", background=C["primary_dark"], foreground="#bbdefb",
                        font=("Segoe UI", 9), padding=(0, 8))
        
    def _crear_banner(self):
        frame = tk.Frame(self.ventana, bg=self.COLORES["primary_dark"])
        frame.pack(fill=tk.X, side=tk.TOP)
        lbl = tk.Label(frame, text="Sistema de Emisión de Cheques",
                       bg=self.COLORES["primary_dark"], fg="white",
                       font=("Segoe UI", 15, "bold"), padx=15, pady=6, anchor=tk.W)
        lbl.pack(side=tk.LEFT)
        self._banner_sub = tk.Label(frame, text="",
                                    bg=self.COLORES["primary_dark"], fg="#bbdefb",
                                    font=("Segoe UI", 9), anchor=tk.E)
        self._banner_sub.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 15), pady=6)
        tk.Frame(self.ventana, bg=self.COLORES["primary"], height=2).pack(fill=tk.X, side=tk.TOP)

    def _crear_statusbar(self):
        frame = tk.Frame(self.ventana, bg="#263238")
        frame.pack(fill=tk.X, side=tk.BOTTOM)
        self._status_izq = tk.Label(frame, text="Listo", bg="#263238", fg="#eceff1",
                                    font=("Segoe UI", 9), padx=10, pady=3, anchor=tk.W)
        self._status_izq.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._status_der = tk.Label(frame, text="", bg="#263238", fg="#90a4ae",
                                    font=("Segoe UI", 9), padx=10, pady=3, anchor=tk.E)
        self._status_der.pack(side=tk.RIGHT)

    def _crear_menu(self):
        menubar = tk.Menu(self.ventana)
        self.ventana.config(menu=menubar)
        
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)
        menu_archivo.add_command(label="Carga Masiva...", command=self._ventana_carga_masiva)
        menu_archivo.add_command(label="Exportar Historial...", command=self._exportar_csv)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self._confirmar_salir)
        
        menu_config = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configuración", menu=menu_config)
        menu_config.add_command(label="Calibrar Impresión", command=self._ventana_calibracion)
        
        menu_ayuda = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)
        menu_ayuda.add_command(label="Acerca de", command=self._about)
    
    def _crear_notebook(self):
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(5, 8))
        
        # Pestaña 1: Ingreso
        frame_ingreso = ttk.Frame(self.notebook)
        self.notebook.add(frame_ingreso, text="Ingreso de Cheque")
        self._crear_tab_ingreso(frame_ingreso)
        
        # Pestaña 2: Historial
        frame_historial = ttk.Frame(self.notebook)
        self.notebook.add(frame_historial, text="Historial")
        self._crear_tab_historial(frame_historial)
    
    def _crear_tab_ingreso(self, frame_padre):
        contenedor = ttk.Frame(frame_padre)
        contenedor.pack(expand=True, fill=tk.BOTH, padx=50, pady=20)

        # Toolbar
        tb = tk.Frame(contenedor, bg=self.COLORES["surface"], bd=0,
                      highlightbackground=self.COLORES["border"], highlightthickness=1)
        tb.pack(fill=tk.X, pady=(0, 18))

        tk.Label(tb, text="Plantilla:", bg=self.COLORES["surface"],
                 font=("Segoe UI", 9, "bold"), fg=self.COLORES["secondary"]).pack(side=tk.LEFT, padx=(12, 4))
        plantillas = self.generador_pdf.listar_plantillas()
        self.combo_plantilla = ttk.Combobox(tb, values=plantillas, state="readonly", width=22)
        if plantillas:
            plantilla_def = self.config_mgr.plantilla_actual or plantillas[0]
            self.combo_plantilla.set(plantilla_def)
        self.combo_plantilla.bind("<<ComboboxSelected>>", self._guardar_config_general)
        self.combo_plantilla.pack(side=tk.LEFT, padx=4)

        # Configuración de rotación (Alimentación Vertical)
        self.var_rotar = tk.BooleanVar(value=self.config_mgr.rotar_90)
        chk_rotar = tk.Checkbutton(tb, text="Alimentación Vertical", variable=self.var_rotar,
                                  bg=self.COLORES["surface"], font=("Segoe UI", 9),
                                  activebackground=self.COLORES["surface"],
                                  command=self._guardar_config_general)
        chk_rotar.pack(side=tk.LEFT, padx=(15, 0))

        tk.Label(tb, text="Impresora:", bg=self.COLORES["surface"],
                 font=("Segoe UI", 9, "bold"), fg=self.COLORES["secondary"]).pack(side=tk.LEFT, padx=(18, 4))
        impresoras = self.generador_pdf.listar_impresoras()
        self.combo_impresora = ttk.Combobox(tb, values=impresoras, state="readonly", width=28)
        impresora_def = self.config_mgr.impresora_predeterminada
        if impresora_def in impresoras:
            self.combo_impresora.set(impresora_def)
        elif impresoras:
            self.combo_impresora.set(impresoras[0])
        self.combo_impresora.pack(side=tk.LEFT, padx=4)
        self.combo_impresora.bind("<<ComboboxSelected>>", self._guardar_impresora_config)

        # Check card
        CARD_BG = "#ffffff"
        card = tk.Frame(contenedor, bg=CARD_BG, bd=0,
                        highlightbackground=self.COLORES["border"], highlightthickness=1)
        card.pack(fill=tk.X, pady=6)
        inner = tk.Frame(card, bg=CARD_BG, padx=28, pady=24)
        inner.pack(fill=tk.X)

        # Fila 1
        f1 = tk.Frame(inner, bg=CARD_BG)
        f1.pack(fill=tk.X, pady=6)
        _lbl = lambda parent, text, **kw: tk.Label(parent, text=text, bg=CARD_BG,
                    font=("Segoe UI", 10, "bold"), fg="#37474f", **kw)

        _lbl(f1, "Serie:").pack(side=tk.LEFT)
        self.entry_serie = tk.Entry(f1, width=8, font=("Segoe UI", 11),
                                    bd=1, relief=tk.SOLID, highlightbackground=self.COLORES["border"])
        self.entry_serie.pack(side=tk.LEFT, padx=5)
        _lbl(f1, "Número:").pack(side=tk.LEFT, padx=(15, 0))
        self.entry_numero = tk.Entry(f1, width=14, font=("Segoe UI", 11),
                                     bd=1, relief=tk.SOLID, highlightbackground=self.COLORES["border"],
                                     validate="key", validatecommand=self.vcmd_numerico)
        self.entry_numero.pack(side=tk.LEFT, padx=5)

        monto_bg = "#e8f5e9"
        fm = tk.Frame(f1, bg=monto_bg, bd=1, relief=tk.SOLID,
                      highlightbackground="#a5d6a7", padx=12, pady=5)
        fm.pack(side=tk.RIGHT)
        tk.Label(fm, text="Gs.", bg=monto_bg, font=("Segoe UI", 12, "bold"),
                 fg=self.COLORES["success"]).pack(side=tk.LEFT)
        self.entry_importe = tk.Entry(fm, width=16, font=("Segoe UI", 13, "bold"),
                                      bd=0, bg=monto_bg, fg=self.COLORES["success"],
                                      textvariable=self.var_importe, justify="right",
                                      validate="key", validatecommand=self.vcmd_numerico)
        self.entry_importe.pack(side=tk.LEFT, padx=5)

        # Fila 2
        f2 = tk.Frame(inner, bg=CARD_BG)
        f2.pack(fill=tk.X, pady=8)
        _lbl(f2, "Fecha:").pack(side=tk.LEFT)
        if TIENE_TKCALENDAR:
            self.date_emision = DateEntry(f2, width=12, font=("Segoe UI", 10))
            self.date_emision.pack(side=tk.LEFT, padx=5)
        else:
            self.spinbox_dia = tk.Spinbox(f2, from_=1, to=31, width=3, font=("Segoe UI", 10))
            self.spinbox_dia.pack(side=tk.LEFT, padx=2)
            self.spinbox_mes = tk.Spinbox(f2, from_=1, to=12, width=3, font=("Segoe UI", 10))
            self.spinbox_mes.pack(side=tk.LEFT, padx=2)
        _lbl(f2, "Páguese a la orden de:").pack(side=tk.LEFT, padx=(25, 0))
        self.entry_beneficiario = tk.Entry(f2, font=("Segoe UI", 11),
                                           bd=0, highlightthickness=1,
                                           highlightbackground=self.COLORES["border"])
        self.entry_beneficiario.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Fila 3
        f3 = tk.Frame(inner, bg=CARD_BG)
        f3.pack(fill=tk.X, pady=8)
        _lbl(f3, "La suma de:").pack(side=tk.LEFT)
        self.lbl_importe_letras = tk.Label(f3, text="...", bg="#f5f5f5",
                                           font=("Segoe UI", 10, "italic"),
                                           fg="#546e7a", anchor="w", padx=10)
        self.lbl_importe_letras.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Fila 4
        f4 = tk.Frame(inner, bg=CARD_BG)
        f4.pack(fill=tk.X, pady=8)
        _lbl(f4, "Concepto:").pack(side=tk.LEFT, anchor=tk.N)
        self.text_concepto = tk.Text(f4, height=2, font=("Segoe UI", 10),
                                     bd=1, relief=tk.SOLID,
                                     highlightbackground=self.COLORES["border"])
        self.text_concepto.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Botones
        btn_frame = tk.Frame(contenedor, bg=self.COLORES["bg"])
        btn_frame.pack(fill=tk.X, pady=(15, 5))

        btn_data = [
            ("Vista Previa", self._vista_previa, "Primary.TButton"),
            ("Imprimir", self._imprimir, "Primary.TButton"),
            ("Guardar", self._guardar_cheque, "TButton"),
            ("Limpiar", self._limpiar_form, "TButton"),
        ]
        for txt, cmd, style in btn_data:
            ttk.Button(btn_frame, text=txt, command=cmd, style=style, width=14).pack(side=tk.LEFT, padx=4)

        ttk.Button(btn_frame, text="Salir", command=self._confirmar_salir, width=10).pack(side=tk.RIGHT, padx=4)
    
    def _crear_tab_historial(self, frame_padre):
        bg = self.COLORES["bg"]

        # 1. Acciones inferiores (Se empaquetan PRIMERO con side=tk.BOTTOM)
        # Esto garantiza que siempre sean visibles y la tabla use el espacio restante
        acc = ttk.LabelFrame(frame_padre, text="Cheque Seleccionado", padding=8)
        acc.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(5, 10))

        ttk.Button(acc, text="🖨 Reimprimir", style="Primary.TButton",
                   command=self._reimprimir_seleccionado).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="👁 Vista Previa",
                   command=self._vista_previa_seleccionado).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="❌ Anular",
                   command=self._anular_cheque_seleccionado).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="✅ Reactivar",
                   command=self._reactivar_cheque_seleccionado).pack(side=tk.LEFT, padx=4)
        ttk.Button(acc, text="📂 Abrir PDFs",
                   command=self._abrir_carpeta_pdfs).pack(side=tk.RIGHT, padx=4)

        # 2. Barra de resumen superior
        sum_frame = tk.Frame(frame_padre, bg=self.COLORES["surface"],
                             highlightbackground=self.COLORES["border"], highlightthickness=1)
        sum_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 5))
        self._lbl_sum = tk.Label(sum_frame, text="0 cheques  |  Total: Gs. 0",
                                 bg=self.COLORES["surface"], fg=self.COLORES["secondary"],
                                 font=("Segoe UI", 10), anchor=tk.W, padx=12, pady=5)
        self._lbl_sum.pack(side=tk.LEFT)
        btn_export = tk.Button(sum_frame, text="Exportar CSV", bg="#e3f2fd",
                               font=("Segoe UI", 9), fg=self.COLORES["primary"],
                               bd=1, relief=tk.SOLID, padx=10,
                               command=self._exportar_csv)
        btn_export.pack(side=tk.RIGHT, padx=8, pady=3)

        # 3. Filtros
        filtros = ttk.LabelFrame(frame_padre, text="Filtros", padding=8)
        filtros.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        labels = [
            ("Serie:", 0, 0), ("Número Desde:", 1, 0), ("Fecha Desde:", 2, 0),
            ("Beneficiario:", 0, 2), ("Hasta:", 1, 2), ("Fecha Hasta:", 2, 2),
        ]
        self._entries_filtro = {}
        for txt, r, c in labels:
            tk.Label(filtros, text=txt, font=("Segoe UI", 9, "bold"),
                     fg=self.COLORES["secondary"]).grid(row=r, column=c, sticky=tk.W, padx=5, pady=3)

        self.entry_filtro_serie = ttk.Entry(filtros, width=10)
        self.entry_filtro_serie.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.entry_filtro_beneficiario = ttk.Entry(filtros, width=20)
        self.entry_filtro_beneficiario.grid(row=0, column=3, sticky=tk.W, padx=5)

        self.spinbox_filtro_num_desde = ttk.Spinbox(filtros, from_=0, to=999999, width=10)
        self.spinbox_filtro_num_desde.grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        self.spinbox_filtro_num_hasta = ttk.Spinbox(filtros, from_=0, to=999999, width=10)
        self.spinbox_filtro_num_hasta.grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)

        if TIENE_TKCALENDAR:
            self.date_filtro_desde = DateEntry(filtros, width=12)
            self.date_filtro_desde.grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
            self.date_filtro_hasta = DateEntry(filtros, width=12)
            self.date_filtro_hasta.grid(row=2, column=3, sticky=tk.W, padx=5, pady=3)
        else:
            self.date_filtro_desde = ttk.Entry(filtros, width=12)
            self.date_filtro_desde.insert(0, "dd/mm")
            self.date_filtro_desde.grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
            self.date_filtro_hasta = ttk.Entry(filtros, width=12)
            self.date_filtro_hasta.insert(0, "dd/mm")
            self.date_filtro_hasta.grid(row=2, column=3, sticky=tk.W, padx=5, pady=3)

        btn_frame = tk.Frame(filtros, bg=self.COLORES["bg"])
        btn_frame.grid(row=0, column=5, rowspan=3, sticky=tk.N, padx=(15, 0), pady=3)
        ttk.Button(btn_frame, text="Filtrar", command=self._aplicar_filtros).pack(pady=2)
        ttk.Button(btn_frame, text="Limpiar", command=self._limpiar_filtros).pack(pady=2)
        ttk.Button(btn_frame, text="Recargar (F5)", command=self._recargar_historial).pack(pady=2)

        # 4. Tabla (Se empaqueta al FINAL para que use el espacio expandible central)
        tabla_container = ttk.Frame(frame_padre)
        tabla_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        sy = ttk.Scrollbar(tabla_container)
        sx = ttk.Scrollbar(tabla_container, orient=tk.HORIZONTAL)

        self.tree_historial = ttk.Treeview(
            tabla_container,
            columns=("id", "serie", "numero", "beneficiario", "importe", "fecha", "concepto", "estado"),
            height=10,
            yscrollcommand=sy.set,
            xscrollcommand=sx.set
        )
        sy.config(command=self.tree_historial.yview)
        sx.config(command=self.tree_historial.xview)

        col_widths = {"#0": 0, "id": 40, "serie": 60, "numero": 80, "beneficiario": 200,
                      "importe": 120, "fecha": 80, "concepto": 250, "estado": 80}
        for col, w in col_widths.items():
            self.tree_historial.column(col, anchor=tk.CENTER, width=w)
        self.tree_historial.column("beneficiario", anchor=tk.W)
        self.tree_historial.column("concepto", anchor=tk.W)
        self.tree_historial.column("importe", anchor=tk.E)

        headings = [("#0", ""), ("id", "ID"), ("serie", "Serie"), ("numero", "Número"),
                    ("beneficiario", "Beneficiario"), ("importe", "Importe"),
                    ("fecha", "Fecha"), ("concepto", "Concepto"), ("estado", "Estado")]
        for col, txt in headings:
            self.tree_historial.heading(col, text=txt)

        self.tree_historial.grid(row=0, column=0, sticky=tk.NSEW)
        sy.grid(row=0, column=1, sticky=tk.NS)
        sx.grid(row=1, column=0, sticky=tk.EW)
        tabla_container.grid_rowconfigure(0, weight=1)
        tabla_container.grid_columnconfigure(0, weight=1)

        self.ventana.bind("<F5>", lambda e: self._recargar_historial())
        self._recargar_historial()
    
    def _on_importe_change(self, *args):
        """Manejador de eventos para cuando cambia el texto del importe."""
        # Evitar recursión
        if hasattr(self, '_bloqueo_importe') and self._bloqueo_importe:
            return

        self._bloqueo_importe = True
        try:
            valor_actual = self.var_importe.get()
            pos_cursor = self.entry_importe.index(tk.INSERT)
            
            # Limpiar y obtener solo números
            valor_limpio = "".join(filter(str.isdigit, valor_actual))
            
            if not valor_limpio:
                self.var_importe.set("")
                self.lbl_importe_letras.config(text="")
                self._bloqueo_importe = False
                return

            importe = int(valor_limpio)
            valor_formateado = f"{importe:,}".replace(",", ".")
            
            if valor_actual != valor_formateado:
                # Calcular la posición del cursor basada en los dígitos reales
                # Esto evita que el cursor salte al principio o se mueva mal
                no_numericos_antes = len([c for c in valor_actual[:pos_cursor] if not c.isdigit()])
                pos_real = pos_cursor - no_numericos_antes
                
                self.var_importe.set(valor_formateado)
                
                # Calcular nueva posición: buscamos dónde quedaría el pos_real en el nuevo string
                nueva_pos = 0
                digitos_contados = 0
                for i, char in enumerate(valor_formateado):
                    if char.isdigit():
                        digitos_contados += 1
                    nueva_pos = i + 1
                    if digitos_contados == pos_real:
                        break
                
                # Usar after_idle para asegurar que el cursor se coloque después de que la UI se actualice
                self.ventana.after_idle(lambda: self.entry_importe.icursor(nueva_pos))

            # Actualizar letras
            try:
                if importe > 0:
                    letras = numero_a_letras(importe)
                    self.lbl_importe_letras.config(text=letras)
                else:
                    self.lbl_importe_letras.config(text="")
            except ValueError:
                self.lbl_importe_letras.config(text="CANTIDAD FUERA DE RANGO")
            
        finally:
            self._bloqueo_importe = False

    def _obtener_fecha_db(self):
        """Obtiene la fecha del formulario en formato estándar para la BD."""
        if TIENE_TKCALENDAR:
            fecha_obj = self.date_emision.get_date()
            return f"{fecha_obj.day:02d}/{fecha_obj.month:02d}/{fecha_obj.year}"
        else:
            dia = int(self.spinbox_dia.get())
            mes = int(self.spinbox_mes.get())
            anio = date.today().year
            from datetime import date as dt_date
            dt_date(anio, mes, dia)
            return f"{dia:02d}/{mes:02d}/{anio}"

    def _obtener_fecha_cheque(self):
        """Obtiene la fecha del formulario en formato espaciado para el cheque (solo DD y MM)."""
        if TIENE_TKCALENDAR:
            fecha_obj = self.date_emision.get_date()
            # Formato DD      MM para alinear con el preimpreso (sin año)
            return f"{fecha_obj.day:02d}      {fecha_obj.month:02d}"
        else:
            dia = self.spinbox_dia.get().zfill(2)
            mes = self.spinbox_mes.get().zfill(2)
            return f"{dia}      {mes}"

    def _obtener_filtro_fecha(self, widget):
        """Devuelve la fecha del filtro en formato dd/mm/yyyy o None."""
        try:
            if TIENE_TKCALENDAR and hasattr(widget, "get_date"):
                fecha_obj = widget.get_date()
                return f"{fecha_obj.day:02d}/{fecha_obj.month:02d}/{fecha_obj.year}"
            fecha = widget.get().strip()
            if not fecha or fecha.lower() == "dd/mm":
                return None
            partes = fecha.split("/")
            dia = int(partes[0])
            mes = int(partes[1])
            if len(partes) >= 3:
                anio = int(partes[2])
            else:
                anio = date.today().year
            from datetime import date as dt_date
            dt_date(anio, mes, dia)
            return f"{dia:02d}/{mes:02d}/{anio}"
        except (ValueError, IndexError, AttributeError):
            return None
    
    def _vista_previa(self):
        """Abre vista previa del cheque en PDF temporal."""
        if not self._validar_formulario():
            return
        
        datos_raw = self._obtener_datos_formulario()
        datos = self._preparar_datos_para_pdf(datos_raw)
        # Generar PDF temporal (se sobrescribe siempre el mismo archivo)
        ruta_pdf = self.generador_pdf.generar_pdf(
            datos, 
            nombre_plantilla=self.combo_plantilla.get(),
            es_temporal=True
        )
        
        if ruta_pdf:
            if self.generador_pdf.abrir_vista_previa(ruta_pdf):
                messagebox.showinfo("Éxito", "PDF abierto en vista previa")
            else:
                messagebox.showerror("Error", "No se pudo abrir el PDF")
    
    def _imprimir(self):
        """Imprime el cheque y lo guarda automáticamente en la base de datos."""
        if not self._validar_formulario():
            return
        
        datos_raw = self._obtener_datos_formulario()
        datos = self._preparar_datos_para_pdf(datos_raw)
        
        # 1. Verificar duplicado antes de hacer nada
        if self.db.verificar_duplicado(datos["serie"], int(datos["numero"])):
            messagebox.showerror("Error", f"El cheque {datos['serie']}-{datos['numero']} ya existe en la base de datos.")
            return

        # 2. Generar el PDF real (no el temporal)
        ruta_pdf = self.generador_pdf.generar_pdf(datos, nombre_plantilla=self.combo_plantilla.get())
        
        if ruta_pdf:
            impresora = self.combo_impresora.get()
            # 3. Intentar imprimir
            if self.generador_pdf.imprimir_directamente(ruta_pdf, nombre_impresora=impresora):
                # 4. Si la impresión se envió, guardar en la BD
                if self.db.insertar_cheque(
                    datos_raw["serie"],
                    int(datos_raw["numero"]),
                    datos_raw["fecha_db"],
                    datos_raw["beneficiario"],
                    datos_raw["importe_num"],
                    datos_raw["importe_letras"],
                    datos_raw["concepto"],
                    datos_raw.get("plantilla", "")
                ):
                    messagebox.showinfo("Éxito", f"Cheque impreso y guardado correctamente.\nImpresora: {impresora}")
                    self._limpiar_form()
                    self._recargar_historial()
                else:
                    messagebox.showerror("Error", "El cheque se envió a imprimir pero no se pudo guardar en la base de datos.")
            else:
                messagebox.showerror("Error", "No se pudo enviar el cheque a la impresora.")
    
    def _guardar_impresora_config(self, event=None):
        """Guarda la impresora seleccionada."""
        self.config_mgr.impresora_predeterminada = self.combo_impresora.get()
        self.config_mgr.guardar()
    
    def _guardar_config_general(self, event=None):
        """Guarda la configuración actual usando el gestor centralizado."""
        # Actualizar variables desde la UI
        self.config_mgr.plantilla_actual = self.combo_plantilla.get()
        self.config_mgr.rotar_90 = self.var_rotar.get()
        self.config_mgr.guardar()
        
        # Notificar al generador PDF que la config cambió
        self.generador_pdf.config = self.config_mgr.a_dict()
    
    def _guardar_cheque(self):
        """Guarda el cheque en BD y genera PDF."""
        if not self._validar_formulario():
            return

        
        datos_raw = self._obtener_datos_formulario()
        datos = self._preparar_datos_para_pdf(datos_raw)
        
        # Verificar duplicado
        if self.db.verificar_duplicado(datos["serie"], int(datos["numero"])):
            messagebox.showerror("Error", f"El cheque {datos['serie']}-{datos['numero']} ya existe")
            return
        
        # Generar PDF
        ruta_pdf = self.generador_pdf.generar_pdf(datos, nombre_plantilla=self.combo_plantilla.get())
        if not ruta_pdf:
            messagebox.showerror("Error", "No se pudo generar el PDF")
            return
        
        # Insertar en BD
        if self.db.insertar_cheque(
            datos_raw["serie"],
            int(datos_raw["numero"]),
            datos_raw["fecha_db"],
            datos_raw["beneficiario"],
            datos_raw["importe_num"],
            datos_raw["importe_letras"],
            datos_raw["concepto"],
            datos_raw.get("plantilla", "")
        ):
            messagebox.showinfo("Éxito", f"Cheque guardado y PDF generado\n{ruta_pdf}")
            self._limpiar_form()
            self._recargar_historial()
        else:
            messagebox.showerror("Error", "No se pudo guardar el cheque en la BD")
    
    def _limpiar_form(self):
        """Limpia los campos del formulario."""
        self.entry_serie.delete(0, tk.END)
        self.entry_numero.delete(0, tk.END)
        self.entry_beneficiario.delete(0, tk.END)
        self.entry_importe.delete(0, tk.END)
        self.text_concepto.delete("1.0", tk.END)
        self.lbl_importe_letras.config(text="")
    
    def _validar_formulario(self):
        """Valida que los campos obligatorios estén llenos y cumplan con los requisitos."""
        # Validar serie
        serie = self.entry_serie.get().strip()
        if not serie:
            messagebox.showerror("Error", "Ingresa la serie del cheque")
            return False
        if len(serie) > 10:
            messagebox.showerror("Error", "La serie no puede exceder 10 caracteres")
            return False
        if not serie.isalnum():
            messagebox.showerror("Error", "La serie debe ser alfanumérica (solo letras y números)")
            return False
        
        # Validar número
        numero = self.entry_numero.get().strip()
        if not numero:
            messagebox.showerror("Error", "Ingresa el número del cheque")
            return False
        try:
            num_int = int(numero)
            if num_int < 1 or num_int > 999999999999:
                messagebox.showerror("Error", "El número debe estar entre 1 y 999,999,999,999")
                return False
        except ValueError:
            messagebox.showerror("Error", "El número debe ser un valor numérico válido")
            return False
        
        # Validar beneficiario
        beneficiario = self.entry_beneficiario.get().strip()
        if not beneficiario:
            messagebox.showerror("Error", "Ingresa el beneficiario")
            return False
        if len(beneficiario) > 100:
            messagebox.showerror("Error", "El beneficiario no puede exceder 100 caracteres")
            return False
        
        # Validar importe
        importe_val = self.entry_importe.get().replace(".", "").replace(",", "")
        if not importe_val:
            messagebox.showerror("Error", "Ingresa un importe")
            return False
        try:
            importe_num = int(importe_val)
            if importe_num <= 0:
                messagebox.showerror("Error", "Ingresa un importe mayor a 0")
                return False
            if importe_num > 9999999999:
                messagebox.showerror("Error", "El importe máximo es 9,999,999,999")
                return False
        except ValueError:
            messagebox.showerror("Error", "El importe debe ser un valor numérico válido")
            return False
        
        # Validar fecha
        if TIENE_TKCALENDAR:
            try:
                fecha_obj = self.date_emision.get_date()
                from datetime import timedelta
                if fecha_obj > (date.today() + timedelta(days=30)):
                    messagebox.showerror("Error", "La fecha no puede ser más de 30 días en el futuro")
                    return False
            except (ValueError, AttributeError, TypeError):
                messagebox.showerror("Error", "La fecha no es válida")
                return False
        else:
            try:
                from datetime import date as dt_date
                dia = int(self.spinbox_dia.get())
                mes = int(self.spinbox_mes.get())
                anio = date.today().year
                dt_date(anio, mes, dia)
            except ValueError:
                messagebox.showerror("Error", "La fecha no es válida (día o mes incorrecto)")
                return False
        
        return True
    
    def _obtener_datos_formulario(self):
        """Obtiene los datos del formulario con sanitización."""
        # Obtener valores y sanitizar
        serie = self._sanitizar_string(self.entry_serie.get(), max_longitud=10)
        numero = self.entry_numero.get().strip()
        beneficiario = self._sanitizar_string(self.entry_beneficiario.get(), max_longitud=100)
        importe_val = self.entry_importe.get().strip()
        concepto = self._sanitizar_string(self.text_concepto.get("1.0", tk.END), max_longitud=200, permitir_caracteres_especiales=True)
        
        # Limpiar el importe de puntos/comas si el usuario los puso manualmente
        importe_limpio = importe_val.replace(".", "").replace(",", "")
        try:
            importe_num = int(importe_limpio)
        except ValueError:
            importe_num = 0

        return {
            "serie": serie,
            "numero": numero,
            "fecha": self._obtener_fecha_cheque(),
            "fecha_db": self._obtener_fecha_db(),
            "beneficiario": beneficiario,
            "importe_num": importe_num,
            "importe_letras": self.lbl_importe_letras.cget("text"),
            "concepto": concepto,
            "serie_numero": f"{serie}-{numero}",
            "plantilla": self.combo_plantilla.get()
        }
    
    def _recargar_historial(self):
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)

        historial = self.db.obtener_ultimos(100)
        total = 0

        for cheque in historial:
            try:
                imp = int(cheque["importe_num"])
                total += imp
                imp_fmt = f"{imp:,}".replace(",", ".")
            except (ValueError, TypeError):
                imp_fmt = cheque["importe_num"]

            estado = cheque.get("estado", "activo")
            self.tree_historial.insert("", tk.END, values=(
                cheque["id"], cheque["serie"], cheque["numero"],
                cheque["beneficiario"], imp_fmt,
                cheque["fecha_emision"], cheque.get("concepto", ""), estado))

        n = len(historial)
        self._lbl_sum.config(
            text=f"{n} cheque{'s' if n != 1 else ''}  |  Total: Gs. {total:,}".replace(",", "."))
        self._actualizar_statusbar()
    
    def _aplicar_filtros(self):
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)

        serie = self.entry_filtro_serie.get() or None
        beneficiario = self.entry_filtro_beneficiario.get() or None
        num_desde = int(self.spinbox_filtro_num_desde.get()) if self.spinbox_filtro_num_desde.get() else None
        num_hasta = int(self.spinbox_filtro_num_hasta.get()) if self.spinbox_filtro_num_hasta.get() else None
        fecha_desde = self._obtener_filtro_fecha(self.date_filtro_desde)
        fecha_hasta = self._obtener_filtro_fecha(self.date_filtro_hasta)

        historial = self.db.filtrar_cheques(
            serie=serie, numero_desde=num_desde, numero_hasta=num_hasta,
            fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
            beneficiario=beneficiario)

        total = 0
        for cheque in historial:
            try:
                imp = int(cheque["importe_num"])
                total += imp
                imp_fmt = f"{imp:,}".replace(",", ".")
            except (ValueError, TypeError):
                imp_fmt = cheque["importe_num"]

            estado = cheque.get("estado", "activo")
            self.tree_historial.insert("", tk.END, values=(
                cheque["id"], cheque["serie"], cheque["numero"],
                cheque["beneficiario"], imp_fmt,
                cheque["fecha_emision"], cheque.get("concepto", ""), estado))

        n = len(historial)
        self._lbl_sum.config(
            text=f"{n} cheque{'s' if n != 1 else ''}  |  Total: Gs. {total:,}".replace(",", "."))
    
    def _limpiar_filtros(self):
        """Limpia los filtros y recarga el historial."""
        self.entry_filtro_serie.delete(0, tk.END)
        self.entry_filtro_beneficiario.delete(0, tk.END)
        self.spinbox_filtro_num_desde.delete(0, tk.END)
        self.spinbox_filtro_num_hasta.delete(0, tk.END)
        self.date_filtro_desde.delete(0, tk.END)
        self.date_filtro_hasta.delete(0, tk.END)
        if not TIENE_TKCALENDAR:
            self.date_filtro_desde.insert(0, "dd/mm")
            self.date_filtro_hasta.insert(0, "dd/mm")
        self._recargar_historial()
    
    def _exportar_csv(self):
        from tkinter import filedialog
        import csv
        ruta = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")])
        if not ruta:
            return
        filas = []
        for item in self.tree_historial.get_children():
            filas.append(self.tree_historial.item(item)["values"])
        encabezados = ["ID", "Serie", "Número", "Beneficiario",
                       "Importe", "Fecha", "Concepto", "Estado"]
        with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(encabezados)
            w.writerows(filas)

    def _obtener_cheque_seleccionado(self):
        """Obtiene el cheque correspondiente a la selección en el historial."""
        seleccion = self.tree_historial.selection()
        if not seleccion:
            return None
        item = self.tree_historial.item(seleccion[0])
        cheque_id = item["values"][0]
        return self.db.obtener_cheque(cheque_id)
    
    def _preparar_datos_para_pdf(self, cheque_dict):
        """Prepara un diccionario de datos formateado específicamente para el PDF."""
        # Asegurar que importe_num sea un entero para el formateo
        try:
            val = cheque_dict.get("importe_num")
            if isinstance(val, str):
                val = val.replace(".", "").replace(",", "")
            importe_int = int(val or 0)
            importe_formateado = f"{importe_int:,}".replace(",", ".")
        except (ValueError, TypeError):
            importe_formateado = str(cheque_dict.get("importe_num", "0"))

        # Formatear fecha para el cheque (DD      MM)
        # El diccionario puede venir del formulario ('fecha') o de la BD ('fecha_emision')
        fecha_original = cheque_dict.get("fecha") or cheque_dict.get("fecha_emision")
        
        try:
            if not fecha_original:
                fecha_cheque = ""
            elif " " in str(fecha_original): # Ya tiene espacios (posiblemente viene del formulario)
                fecha_cheque = str(fecha_original).strip()
            else:
                partes = str(fecha_original).split("/")
                # Solo tomamos día y mes, y agregamos los espacios para los casilleros
                fecha_cheque = f"{partes[0].zfill(2)}      {partes[1].zfill(2)}"
        except (ValueError, IndexError, AttributeError):
            fecha_cheque = str(fecha_original or "")

        return {
            "serie": cheque_dict.get("serie", ""),
            "numero": cheque_dict.get("numero", 0),
            "fecha": fecha_cheque,
            "fecha_db": cheque_dict.get("fecha_db") or cheque_dict.get("fecha_emision", ""),
            "beneficiario": cheque_dict.get("beneficiario", ""),
            "importe_num": importe_formateado,
            "importe_num_raw": cheque_dict.get("importe_num") or 0,
            "importe_letras": cheque_dict.get("importe_letras", ""),
            "concepto": cheque_dict.get("concepto", ""),
            "serie_numero": f"{cheque_dict.get('serie', '')}-{cheque_dict.get('numero', 0)}",
            "plantilla": cheque_dict.get("plantilla", self.combo_plantilla.get())
        }

    def _reimprimir_seleccionado(self):
        """Reimprime el cheque seleccionado en el historial."""
        cheque = self._obtener_cheque_seleccionado()
        if not cheque:
            messagebox.showwarning("Atención", "Selecciona un cheque en el historial")
            return
        
        # Convertir Row de SQLite a dict si es necesario
        cheque_dict = dict(cheque)
        datos = self._preparar_datos_para_pdf(cheque_dict)
        
        ruta_pdf = self.generador_pdf.generar_pdf(datos, nombre_plantilla=datos["plantilla"])
        if ruta_pdf:
            impresora = self.combo_impresora.get()
            if self.generador_pdf.imprimir_directamente(ruta_pdf, nombre_impresora=impresora):
                messagebox.showinfo("Éxito", f"Cheque enviado a: {impresora}")
            else:
                messagebox.showerror("Error", "No se pudo reimprimir el cheque seleccionado")

    def _vista_previa_seleccionado(self):
        """Abre vista previa del cheque seleccionado en el historial (temporal)."""
        cheque = self._obtener_cheque_seleccionado()
        if not cheque:
            messagebox.showwarning("Atención", "Selecciona un cheque en el historial")
            return

        cheque_dict = dict(cheque)
        datos = self._preparar_datos_para_pdf(cheque_dict)

        # Usar modo temporal para no duplicar archivos en PDFs/
        ruta_pdf = self.generador_pdf.generar_pdf(
            datos,
            nombre_plantilla=datos["plantilla"],
            es_temporal=True
        )
        if ruta_pdf and self.generador_pdf.abrir_vista_previa(ruta_pdf):
            messagebox.showinfo("Éxito", "PDF de cheque abierto en vista previa")
        else:
            messagebox.showerror("Error", "No se pudo abrir la vista previa")

    def _anular_cheque_seleccionado(self):
        """Anula el cheque seleccionado en el historial."""
        cheque = self._obtener_cheque_seleccionado()
        if not cheque:
            messagebox.showwarning("Atención", "Selecciona un cheque en el historial")
            return

        cheque_dict = dict(cheque)
        estado_actual = cheque_dict.get("estado", "activo")

        if estado_actual == "anulado":
            messagebox.showwarning("Atención", "Este cheque ya está anulado")
            return

        # Confirmar anulación
        if messagebox.askyesno(
            "Confirmar Anulación",
            f"¿Estás seguro de anular el cheque {cheque_dict['serie']}-{cheque_dict['numero']}?\n\n"
            f"Beneficiario: {cheque_dict['beneficiario']}\n"
            f"Importe: {cheque_dict['importe_num']:,}"
        ):
            if self.db.anular_cheque(cheque_dict["id"]):
                messagebox.showinfo("Éxito", "Cheque anulado correctamente")
                self._recargar_historial()
            else:
                messagebox.showerror("Error", "No se pudo anular el cheque")

    def _reactivar_cheque_seleccionado(self):
        """Reactiva el cheque seleccionado en el historial."""
        cheque = self._obtener_cheque_seleccionado()
        if not cheque:
            messagebox.showwarning("Atención", "Selecciona un cheque en el historial")
            return

        cheque_dict = dict(cheque)
        estado_actual = cheque_dict.get("estado", "activo")

        if estado_actual == "activo":
            messagebox.showwarning("Atención", "Este cheque ya está activo")
            return

        # Confirmar reactivación
        if messagebox.askyesno(
            "Confirmar Reactivación",
            f"¿Estás seguro de reactivar el cheque {cheque_dict['serie']}-{cheque_dict['numero']}?\n\n"
            f"Beneficiario: {cheque_dict['beneficiario']}\n"
            f"Importe: {cheque_dict['importe_num']:,}"
        ):
            if self.db.reactivar_cheque(cheque_dict["id"]):
                messagebox.showinfo("Éxito", "Cheque reactivado correctamente")
                self._recargar_historial()
            else:
                messagebox.showerror("Error", "No se pudo reactivar el cheque")
    
    def _ventana_calibracion(self):
        """Abre ventana interactiva de calibración de impresión."""
        VentanaCalibracion(self.ventana, self.generador_pdf)

    def _ventana_carga_masiva(self):
        """Abre ventana de carga masiva de cheques."""
        VentanaCargaMasiva(self.ventana, self.db)
    
    def _abrir_carpeta_pdfs(self):
        """Abre la carpeta donde se guardan los PDFs generados."""
        import os
        import subprocess
        
        ruta_pdfs = Path(self.generador_pdf.dir_base) / "PDFs"
        
        # Crear la carpeta si no existe
        if not ruta_pdfs.exists():
            ruta_pdfs.mkdir(parents=True, exist_ok=True)
            
        try:
            if sys.platform == "win32":
                os.startfile(ruta_pdfs)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(ruta_pdfs)])
            else:
                subprocess.Popen(["xdg-open", str(ruta_pdfs)])
        except (OSError, FileNotFoundError, PermissionError) as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado al abrir carpeta: {e}")

    def _about(self):
        """Muestra información sobre la aplicación."""
        messagebox.showinfo(
            "Acerca de",
            "Sistema de Emisión de Cheques v1.0\n\n"
            "Aplicación para emitir y gestionar cheques digitales\n"
            "Desarrollo: 2026"
        )

    def _confirmar_salir(self):
        if self._tracker.hay_cambios():
            if not messagebox.askyesno("Confirmar salida",
                                       "Hay datos sin guardar. ¿Salir de todas formas?"):
                return
        self.ventana.destroy()


def main():
    """Función principal."""
    if not TIENE_TKCALENDAR:
        print("Advertencia: tkcalendar no está instalado.")
        print("  Para mejor experiencia, instalalo con: pip install tkcalendar")
        print("  Por ahora se usará el selector de fecha manual.\n")
    
    ventana = tk.Tk()
    app = AplicacionCheques(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
