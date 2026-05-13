"""
Aplicación principal del sistema de cheques.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import date
import sys
from config import obtener_config
from pathlib import Path

# Importar módulos propios
from db import GestionadorCheques
from impresion import GeneradorPDF
from num2letras import numero_a_letras
from calibracion import VentanaCalibracion

# Intentar importar tkcalendar para date picker
try:
    from tkcalendar import DateEntry
    TIENE_TKCALENDAR = True
except ImportError:
    TIENE_TKCALENDAR = False
    print("Advertencia: tkcalendar no instalado. Se usará selector de fecha manual.")


class AplicacionCheques:
    """Aplicación principal de gestión de cheques."""
    
    def __init__(self, ventana_principal):
        """Inicializa la aplicación."""
        self.ventana = ventana_principal
        self.ventana.title("Sistema de Emisión de Cheques")
        self.ventana.geometry("1000x700")
        
        # Inicializar configuración centralizada
        dir_base = Path(__file__).parent
        self.config_mgr = obtener_config(str(dir_base / "config.json"), str(dir_base))
        
        # Inicializar módulos
        ruta_bd = self.config_mgr.ruta_bd
        self.db = GestionadorCheques(str(ruta_bd))
        self.generador_pdf = GeneradorPDF()
        
        # Aplicar Estilos Modernos
        self._aplicar_estilos()
        
        # Variables de control
        self.datos_actuales = {}
        self.var_importe = tk.StringVar()
        self.var_importe.trace_add("write", self._on_importe_change)
        
        # Registrar comando de validación para campos numéricos (con límite de longitud)
        self.vcmd_numerico = (self.ventana.register(self._validar_input_numerico), '%P', '%W')
        
        # Crear interfaz
        self._crear_menu()
        self._crear_notebook()

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
        
        # Caracteres permitidos básicos (letras, números, espacios, puntuación básica)
        caracteres_permitidos = "ABCDEFGHIJKLMNOPQRSTUVWXYZÑ0123456789 .,;-/"
        
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
        """Configura estilos modernos para la interfaz."""
        style = ttk.Style()
        style.theme_use('clam')  # Base más moderna que el default de Windows
        
        # Colores
        bg_color = "#f0f2f5"
        primary_color = "#1a73e8"
        secondary_color = "#5f6368"
        
        self.ventana.configure(bg=bg_color)
        
        # Estilo para Notebook (pestañas)
        style.configure("TNotebook", background=bg_color, borderwidth=0, padding=0)
        style.configure("TNotebook.Tab", 
                        padding=[30, 12], 
                        font=("Segoe UI", 10, "bold"),
                        background="#e0e0e0",
                        foreground=secondary_color,
                        borderwidth=0)
        
        style.map("TNotebook.Tab", 
                  background=[("selected", primary_color), ("active", "#e8f0fe")],
                  foreground=[("selected", "white"), ("active", primary_color)],
                  padding=[("selected", [40, 15]), ("!selected", [30, 12])],
                  font=[("selected", ("Segoe UI", 11, "bold")), ("!selected", ("Segoe UI", 10, "bold"))])
        
        # Estilo para Labels
        style.configure("TLabel", background=bg_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"), foreground=primary_color)
        
        # Estilo para Botones
        style.configure("TButton", padding=10, font=("Segoe UI", 10, "bold"))
        style.configure("Primary.TButton", background=primary_color, foreground="white")
        style.map("Primary.TButton", background=[("active", "#1557b0")])
        
        # Estilo para LabelFrames
        style.configure("TLabelframe", background=bg_color, bordercolor="#dadce0", borderwidth=1)
        style.configure("TLabelframe.Label", background=bg_color, font=("Segoe UI", 10, "bold"), foreground=secondary_color)
        
    def _crear_menu(self):
        """Crea el menú de la aplicación."""
        menubar = tk.Menu(self.ventana)
        self.ventana.config(menu=menubar)
        
        # Menú Archivo
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)
        menu_archivo.add_command(label="Salir", command=self.ventana.quit)
        
        # Menú Ayuda
        menu_ayuda = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=menu_ayuda)
        menu_ayuda.add_command(label="Acerca de", command=self._about)
    
    def _crear_notebook(self):
        """Crea el notebook (pestañas) principal."""
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña 1: Ingreso
        frame_ingreso = ttk.Frame(self.notebook)
        self.notebook.add(frame_ingreso, text="Ingreso de Cheque")
        self._crear_tab_ingreso(frame_ingreso)
        
        # Pestaña 2: Historial
        frame_historial = ttk.Frame(self.notebook)
        self.notebook.add(frame_historial, text="Historial")
        self._crear_tab_historial(frame_historial)
    
    def _crear_tab_ingreso(self, frame_padre):
        """Crea la pestaña de ingreso de cheques con un diseño similar a un cheque real."""
        # Contenedor centrado
        contenedor = ttk.Frame(frame_padre)
        contenedor.pack(expand=True, fill=tk.BOTH, padx=40, pady=20)

        # === Barra de Configuración Superior ===
        frame_config = ttk.Frame(contenedor)
        frame_config.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(frame_config, text="Plantilla:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
        plantillas = self.generador_pdf.listar_plantillas()
        self.combo_plantilla = ttk.Combobox(frame_config, values=plantillas, state="readonly", width=25)
        if plantillas:
            plantilla_def = self.config_mgr.plantilla_actual or plantillas[0]
            self.combo_plantilla.set(plantilla_def)
        self.combo_plantilla.pack(side=tk.LEFT, padx=5)

        ttk.Label(frame_config, text="Impresora:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=15)
        impresoras = self.generador_pdf.listar_impresoras()
        self.combo_impresora = ttk.Combobox(frame_config, values=impresoras, state="readonly", width=30)
        impresora_def = self.config_mgr.impresora_predeterminada
        if impresora_def in impresoras:
            self.combo_impresora.set(impresora_def)
        elif impresoras:
            self.combo_impresora.set(impresoras[0])
        self.combo_impresora.pack(side=tk.LEFT, padx=5)
        self.combo_impresora.bind("<<ComboboxSelected>>", self._guardar_impresora_config)

        # === Representación Visual del Cheque ===
        cheque_bg = "#ffffff"
        frame_cheque = tk.Frame(contenedor, bg=cheque_bg, bd=2, relief=tk.RIDGE, padx=30, pady=30)
        frame_cheque.pack(fill=tk.X, pady=10)

        # Fila 1: Serie, Número e Importe Numérico
        fila1 = tk.Frame(frame_cheque, bg=cheque_bg)
        fila1.pack(fill=tk.X, pady=10)
        
        tk.Label(fila1, text="Serie:", bg=cheque_bg, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.entry_serie = tk.Entry(fila1, width=8, font=("Segoe UI", 11), bd=1, relief=tk.SOLID)
        self.entry_serie.pack(side=tk.LEFT, padx=5)
        
        tk.Label(fila1, text="Número:", bg=cheque_bg, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(15, 0))
        self.entry_numero = tk.Entry(fila1, width=15, font=("Segoe UI", 11), bd=1, relief=tk.SOLID, validate="key", validatecommand=self.vcmd_numerico)
        self.entry_numero.pack(side=tk.LEFT, padx=5)
        
        # Importe a la derecha
        frame_monto = tk.Frame(fila1, bg="#f8f9fa", bd=1, relief=tk.SOLID, padx=10, pady=5)
        frame_monto.pack(side=tk.RIGHT)
        tk.Label(frame_monto, text="Gs.", bg="#f8f9fa", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self.entry_importe = tk.Entry(frame_monto, width=18, font=("Segoe UI", 12, "bold"), bd=0, bg="#f8f9fa", 
                                    textvariable=self.var_importe, justify='right',
                                    validate="key", validatecommand=self.vcmd_numerico)
        self.entry_importe.pack(side=tk.LEFT, padx=5)

        # Fila 2: Fecha y Beneficiario
        fila2 = tk.Frame(frame_cheque, bg=cheque_bg)
        fila2.pack(fill=tk.X, pady=15)

        tk.Label(fila2, text="Fecha:", bg=cheque_bg, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        if TIENE_TKCALENDAR:
            self.date_emision = DateEntry(fila2, width=12, font=("Segoe UI", 10))
            self.date_emision.pack(side=tk.LEFT, padx=5)
        else:
            self.spinbox_dia = tk.Spinbox(fila2, from_=1, to=31, width=3, font=("Segoe UI", 10))
            self.spinbox_dia.pack(side=tk.LEFT, padx=2)
            self.spinbox_mes = tk.Spinbox(fila2, from_=1, to=12, width=3, font=("Segoe UI", 10))
            self.spinbox_mes.pack(side=tk.LEFT, padx=2)

        tk.Label(fila2, text="Páguese a la orden de:", bg=cheque_bg, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(30, 0))
        self.entry_beneficiario = tk.Entry(fila2, font=("Segoe UI", 11), bd=0, highlightthickness=1, highlightbackground="#ced4da")
        self.entry_beneficiario.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Fila 3: Importe en Letras
        fila3 = tk.Frame(frame_cheque, bg=cheque_bg)
        fila3.pack(fill=tk.X, pady=15)
        tk.Label(fila3, text="La suma de:", bg=cheque_bg, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.lbl_importe_letras = tk.Label(fila3, text="...", bg="#f1f3f4", font=("Segoe UI", 10, "italic"), anchor="w", padx=10)
        self.lbl_importe_letras.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Fila 4: Concepto
        fila4 = tk.Frame(frame_cheque, bg=cheque_bg)
        fila4.pack(fill=tk.X, pady=15)
        tk.Label(fila4, text="Concepto:", bg=cheque_bg, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self.text_concepto = tk.Text(fila4, height=2, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.text_concepto.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # === Botones de Acción ===
        frame_acciones = ttk.Frame(contenedor)
        frame_acciones.pack(fill=tk.X, pady=20)
        
        ttk.Button(frame_acciones, text="👁 Vista Previa", command=self._vista_previa, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_acciones, text="🖨 Imprimir", style="Primary.TButton", command=self._imprimir, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_acciones, text="💾 Guardar", command=self._guardar_cheque, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_acciones, text="🧹 Limpiar", command=self._limpiar_form, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_acciones, text="🚪 Salir", command=self.ventana.quit, width=15).pack(side=tk.RIGHT, padx=5)
    
    def _crear_tab_historial(self, frame_padre):
        """Crea la pestaña de historial de cheques."""
        # Frame de filtros
        frame_filtros = ttk.LabelFrame(frame_padre, text="Filtros", padding=10)
        frame_filtros.pack(fill=tk.X, padx=10, pady=10)
        
        # Filtro por serie
        ttk.Label(frame_filtros, text="Serie:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.entry_filtro_serie = ttk.Entry(frame_filtros, width=10)
        self.entry_filtro_serie.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Filtro por beneficiario
        ttk.Label(frame_filtros, text="Beneficiario:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.entry_filtro_beneficiario = ttk.Entry(frame_filtros, width=20)
        self.entry_filtro_beneficiario.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Filtro por rango de números
        ttk.Label(frame_filtros, text="Número Desde:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.spinbox_filtro_num_desde = ttk.Spinbox(frame_filtros, from_=0, to=999999, width=10)
        self.spinbox_filtro_num_desde.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(frame_filtros, text="Hasta:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.spinbox_filtro_num_hasta = ttk.Spinbox(frame_filtros, from_=0, to=999999, width=10)
        self.spinbox_filtro_num_hasta.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Filtro por rango de fecha
        ttk.Label(frame_filtros, text="Fecha Desde:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        if TIENE_TKCALENDAR:
            self.date_filtro_desde = DateEntry(frame_filtros, width=12)
        else:
            self.date_filtro_desde = ttk.Entry(frame_filtros, width=12)
            self.date_filtro_desde.insert(0, "dd/mm")
        self.date_filtro_desde.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(frame_filtros, text="Fecha Hasta:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        if TIENE_TKCALENDAR:
            self.date_filtro_hasta = DateEntry(frame_filtros, width=12)
        else:
            self.date_filtro_hasta = ttk.Entry(frame_filtros, width=12)
            self.date_filtro_hasta.insert(0, "dd/mm")
        self.date_filtro_hasta.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Botones de filtro
        btn_filtrar = ttk.Button(frame_filtros, text="Filtrar", command=self._aplicar_filtros)
        btn_filtrar.grid(row=0, column=6, sticky=tk.W, padx=10)
        
        btn_limpiar_filtros = ttk.Button(frame_filtros, text="Limpiar Filtros", command=self._limpiar_filtros)
        btn_limpiar_filtros.grid(row=1, column=6, sticky=tk.W, padx=10)
        
        btn_recargar = ttk.Button(frame_filtros, text="Recargar (F5)", command=self._recargar_historial)
        btn_recargar.grid(row=2, column=6, sticky=tk.W, padx=10)
        
        # Frame de tabla
        frame_tabla = ttk.Frame(frame_padre)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))
        
        # Crear Treeview con scrollbar
        scrollbar_y = ttk.Scrollbar(frame_tabla)
        scrollbar_x = ttk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL)
        
        # Reducir height significativamente para dejar espacio abajo
        self.tree_historial = ttk.Treeview(
            frame_tabla,
            columns=("id", "serie", "numero", "beneficiario", "importe", "fecha", "concepto"),
            height=10,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        
        scrollbar_y.config(command=self.tree_historial.yview)
        scrollbar_x.config(command=self.tree_historial.xview)
        
        # Configurar columnas
        self.tree_historial.column("#0", width=0, stretch=tk.NO)
        self.tree_historial.column("id", anchor=tk.CENTER, width=40)
        self.tree_historial.column("serie", anchor=tk.CENTER, width=60)
        self.tree_historial.column("numero", anchor=tk.CENTER, width=80)
        self.tree_historial.column("beneficiario", anchor=tk.W, width=200)
        self.tree_historial.column("importe", anchor=tk.E, width=120)
        self.tree_historial.column("fecha", anchor=tk.CENTER, width=80)
        self.tree_historial.column("concepto", anchor=tk.W, width=300)
        
        self.tree_historial.heading("#0", text="", anchor=tk.W)
        self.tree_historial.heading("id", text="ID")
        self.tree_historial.heading("serie", text="Serie")
        self.tree_historial.heading("numero", text="Número")
        self.tree_historial.heading("beneficiario", text="Beneficiario")
        self.tree_historial.heading("importe", text="Importe")
        self.tree_historial.heading("fecha", text="Fecha")
        self.tree_historial.heading("concepto", text="Concepto")
        
        self.tree_historial.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar_y.grid(row=0, column=1, sticky=tk.NS)
        scrollbar_x.grid(row=1, column=0, sticky=tk.EW)
        
        frame_tabla.grid_rowconfigure(0, weight=1)
        frame_tabla.grid_columnconfigure(0, weight=1)
        
        # === Panel de Acciones Inferior ===
        frame_acciones_historial = ttk.LabelFrame(frame_padre, text="Acciones de Cheque Seleccionado", padding=10)
        frame_acciones_historial.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        btn_reimprimir = ttk.Button(
            frame_acciones_historial, 
            text="🖨 Reimprimir", 
            style="Primary.TButton",
            command=self._reimprimir_seleccionado
        )
        btn_reimprimir.pack(side=tk.LEFT, padx=10)
        
        btn_vista_previa_historial = ttk.Button(
            frame_acciones_historial, 
            text="👁 Vista Previa", 
            command=self._vista_previa_seleccionado
        )
        btn_vista_previa_historial.pack(side=tk.LEFT, padx=10)
        
        btn_abrir_pdf = ttk.Button(
            frame_acciones_historial, 
            text="📂 Abrir Carpeta PDFs", 
            command=self._abrir_carpeta_pdfs
        )
        btn_abrir_pdf.pack(side=tk.RIGHT, padx=10)
        
        # Vincular F5 para recargar
        self.ventana.bind("<F5>", lambda e: self._recargar_historial())
        
        # Cargar historial inicial
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
            dia = self.spinbox_dia.get().zfill(2)
            mes = self.spinbox_mes.get().zfill(2)
            anio = date.today().year
            return f"{dia}/{mes}/{anio}"

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
        """Devuelve la fecha del filtro en formato dd/mm o None si no está válida."""
        try:
            if TIENE_TKCALENDAR and hasattr(widget, "get_date"):
                fecha_obj = widget.get_date()
                return f"{fecha_obj.day:02d}/{fecha_obj.month:02d}"
            fecha = widget.get().strip()
            if not fecha or fecha.lower() == "dd/mm":
                return None
            partes = fecha.split("/")
            if len(partes) != 2:
                return None
            dia = int(partes[0])
            mes = int(partes[1])
            return f"{dia:02d}/{mes:02d}"
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
                    datos["serie"],
                    int(datos["numero"]),
                    datos_raw["fecha_db"],
                    datos["beneficiario"],
                    datos_raw["importe_num"], # Ya es int desde _obtener_datos_formulario
                    datos["importe_letras"],
                    datos["concepto"],
                    datos.get("plantilla", "")
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
    
    def _guardar_config_general(self):
        """Guarda la configuración actual usando el gestor centralizado."""
        # Actualizar variables desde la UI
        self.config_mgr.plantilla_actual = self.combo_plantilla.get()
        self.config_mgr.guardar()
    
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
                # Validar que no sea una fecha futura (más de 30 días)
                from datetime import timedelta
                if fecha_obj > (date.today() + timedelta(days=30)):
                    messagebox.showerror("Error", "La fecha no puede ser más de 30 días en el futuro")
                    return False
            except (ValueError, AttributeError, TypeError):
                messagebox.showerror("Error", "La fecha no es válida")
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
        """Recarga el historial de cheques."""
        print("Recargando historial...")
        # Limpiar tabla
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)
        
        # Cargar últimos 100 cheques
        historial = self.db.obtener_ultimos(100)
        print(f"Cheques encontrados en BD: {len(historial)}")
        
        for cheque in historial:
            # Formatear importe con puntos para el historial
            try:
                importe_formateado = f"{int(cheque['importe_num']):,}".replace(",", ".")
            except:
                importe_formateado = cheque['importe_num']

            self.tree_historial.insert(
                "",
                tk.END,
                values=(
                    cheque["id"],
                    cheque["serie"],
                    cheque["numero"],
                    cheque["beneficiario"],
                    importe_formateado,
                    cheque["fecha_emision"],
                    cheque.get("concepto", "")
                )
            )
    
    def _aplicar_filtros(self):
        """Aplica filtros al historial."""
        # Limpiar tabla
        for item in self.tree_historial.get_children():
            self.tree_historial.delete(item)
        
        # Obtener parámetros de filtro
        serie = self.entry_filtro_serie.get() or None
        beneficiario = self.entry_filtro_beneficiario.get() or None
        num_desde = self.spinbox_filtro_num_desde.get()
        num_hasta = self.spinbox_filtro_num_hasta.get()
        fecha_desde = self._obtener_filtro_fecha(self.date_filtro_desde)
        fecha_hasta = self._obtener_filtro_fecha(self.date_filtro_hasta)
        
        num_desde = int(num_desde) if num_desde else None
        num_hasta = int(num_hasta) if num_hasta else None
        
        # Filtrar
        historial = self.db.filtrar_cheques(
            serie=serie,
            numero_desde=num_desde,
            numero_hasta=num_hasta,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            beneficiario=beneficiario
        )
        
        for cheque in historial:
            # Formatear importe con puntos para el historial
            try:
                importe_formateado = f"{int(cheque['importe_num']):,}".replace(",", ".")
            except:
                importe_formateado = cheque['importe_num']

            self.tree_historial.insert(
                "",
                tk.END,
                values=(
                    cheque["id"],
                    cheque["serie"],
                    cheque["numero"],
                    cheque["beneficiario"],
                    importe_formateado,
                    cheque["fecha_emision"],
                    cheque.get("concepto", "")
                )
            )
    
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
    
    def _ventana_calibracion(self):
        """Abre ventana interactiva de calibración de impresión."""
        VentanaCalibracion(self.ventana, self.generador_pdf)
    
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


def main():
    """Función principal."""
    # Instalar tkcalendar si no está disponible
    if not TIENE_TKCALENDAR:
        print("Instalando tkcalendar para mejor experiencia...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tkcalendar"])
            print("✓ tkcalendar instalado correctamente")
        except:
            print("Advertencia: No se pudo instalar tkcalendar automáticamente")
    
    ventana = tk.Tk()
    app = AplicacionCheques(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
