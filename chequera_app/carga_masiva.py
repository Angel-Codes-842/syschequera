"""
Modulo de carga masiva de cheques desde archivos CSV/Excel.
Permite importar multiples cheques de una sola vez con validacion y previsualizacion.
"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from db import GestionadorCheques
from num2letras import numero_a_letras

try:
    import openpyxl
    TIENE_OPENPYXL = True
except ImportError:
    TIENE_OPENPYXL = False

COLUMNAS_ESPERADAS = ["serie", "numero", "fecha_emision", "beneficiario", "importe", "concepto"]


class ValidadorCheque:
    """Valida una fila de datos de cheque."""

    @staticmethod
    def validar_fila(fila: Dict, numero_fila: int) -> Tuple[bool, str]:
        """
        Valida una fila de datos de cheque.
        Retorna (valido, mensaje_error).
        """
        serie = fila.get("serie", "").strip().upper()
        if not serie:
            return False, f"Fila {numero_fila}: serie vacia"
        if len(serie) > 10:
            return False, f"Fila {numero_fila}: serie demasiado larga ({len(serie)} > 10)"
        if not serie.isalnum():
            return False, f"Fila {numero_fila}: serie debe ser alfanumerica"

        try:
            numero = int(str(fila.get("numero", "")).strip())
            if numero < 1 or numero > 999999999999:
                return False, f"Fila {numero_fila}: numero fuera de rango (1-999999999999)"
        except (ValueError, TypeError):
            return False, f"Fila {numero_fila}: numero invalido"

        beneficiario = fila.get("beneficiario", "").strip().upper()
        if not beneficiario:
            return False, f"Fila {numero_fila}: beneficiario vacio"
        if len(beneficiario) > 100:
            return False, f"Fila {numero_fila}: beneficiario demasiado largo"

        fecha = fila.get("fecha_emision", "").strip()
        if not fecha:
            return False, f"Fila {numero_fila}: fecha vacia"
        partes = fecha.split("/")
        if len(partes) != 2:
            return False, f"Fila {numero_fila}: fecha debe ser dd/mm"
        try:
            dia, mes = int(partes[0]), int(partes[1])
            if dia < 1 or dia > 31 or mes < 1 or mes > 12:
                return False, f"Fila {numero_fila}: fecha invalida ({fecha})"
        except ValueError:
            return False, f"Fila {numero_fila}: fecha debe ser numerica (dd/mm)"

        try:
            importe = int(str(fila.get("importe", "")).replace(".", "").replace(",", "").strip())
            if importe <= 0:
                return False, f"Fila {numero_fila}: importe debe ser mayor a 0"
            if importe > 9999999999:
                return False, f"Fila {numero_fila}: importe maximo 9.999.999.999"
        except (ValueError, TypeError):
            return False, f"Fila {numero_fila}: importe invalido"

        return True, ""


class CargaMasiva:
    """Gestiona la carga masiva de cheques desde archivos."""

    def __init__(self, gestor_db: GestionadorCheques):
        self.gestor_db = gestor_db
        self.datos: List[Dict] = []
        self.errores: List[Tuple[int, str]] = []
        self.duplicados: List[Tuple[int, str]] = []

    @staticmethod
    def _detectar_delimitador(muestra: str) -> str:
        """Detecta el delimitador de un CSV probando varios y eligiendo el más consistente."""
        lineas = [l for l in muestra.splitlines() if l.strip()]
        if len(lineas) < 2:
            return ","
        mejores = []
        for delim in [",", ";", "\t", "|"]:
            try:
                import io
                reader = csv.reader(io.StringIO(muestra), delimiter=delim)
                filas = [r for r in reader]
                if len(filas) < 2:
                    continue
                ncols = len(filas[0])
                if ncols < 2:
                    continue
                if all(len(r) == ncols for r in filas):
                    mejores.append((ncols, -len([c for c in muestra if c == delim]), delim))
            except Exception:
                continue
        if mejores:
            mejores.sort(key=lambda x: x[0], reverse=True)
            if len(mejores) > 1 and mejores[0][0] == mejores[1][0]:
                mejores.sort(key=lambda x: x[1])
            return mejores[0][2]
        return ","

    def leer_csv(self, ruta: str) -> Tuple[bool, str]:
        """Lee un archivo CSV y carga los datos."""
        self.datos = []
        self.errores = []
        self.duplicados = []

        try:
            with open(ruta, "r", encoding="utf-8-sig") as f:
                muestra = f.read(4096)
                f.seek(0)

                delimiter = self._detectar_delimitador(muestra)
                reader = csv.DictReader(f, delimiter=delimiter)
                if not reader.fieldnames:
                    return False, "El archivo CSV no tiene encabezados"

                columnas = [c.strip().lower() for c in reader.fieldnames]
                faltan = [c for c in COLUMNAS_ESPERADAS[:5] if c not in columnas]
                if faltan:
                    return False, f"Faltan columnas requeridas: {', '.join(faltan)}"

                return self._procesar_filas(reader, columnas)

        except UnicodeDecodeError:
            return False, "Error de codificacion. Guarda el archivo como UTF-8"
        except FileNotFoundError:
            return False, f"Archivo no encontrado: {ruta}"
        except Exception as e:
            return False, f"Error al leer CSV: {e}"

    def leer_excel(self, ruta: str) -> Tuple[bool, str]:
        """Lee un archivo Excel (.xlsx) y carga los datos."""
        if not TIENE_OPENPYXL:
            return False, "openpyxl no esta instalado. Usa CSV o instala: pip install openpyxl"

        self.datos = []
        self.errores = []
        self.duplicados = []

        try:
            wb = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
            ws = wb.active

            filas = list(ws.iter_rows(values_only=True))
            if not filas:
                return False, "El archivo Excel esta vacio"

            encabezados = [str(c).strip().lower() if c else "" for c in filas[0]]
            faltan = [c for c in COLUMNAS_ESPERADAS[:5] if c not in encabezados]
            if faltan:
                return False, f"Faltan columnas requeridas: {', '.join(faltan)}"

            filas_datos = []
            for fila in filas[1:]:
                if any(v is not None for v in fila):
                    filas_datos.append(fila)

            columnas = {col: idx for idx, col in enumerate(encabezados)}

            reader = []
            for fila in filas_datos:
                d = {}
                for col in COLUMNAS_ESPERADAS:
                    idx = columnas.get(col)
                    if idx is not None and idx < len(fila):
                        d[col] = fila[idx] if fila[idx] is not None else ""
                    else:
                        d[col] = ""
                reader.append(d)

            return self._procesar_filas(reader, COLUMNAS_ESPERADAS)

        except ImportError:
            return False, "openpyxl no disponible"
        except Exception as e:
            return False, f"Error al leer Excel: {e}"

    def _procesar_filas(self, reader, columnas: List[str]) -> Tuple[bool, str]:
        """Procesa y valida todas las filas del archivo."""
        self.datos = []
        self.errores = []
        idx_num = columnas.index("numero") if "numero" in columnas else -1
        idx_conc = columnas.index("concepto") if "concepto" in columnas else -1

        for i, fila in enumerate(reader, start=2):
            if isinstance(fila, dict):
                d = {c: str(fila.get(c, "")).strip() for c in COLUMNAS_ESPERADAS}
            else:
                d = {}
                for col in COLUMNAS_ESPERADAS:
                    idx = columnas.index(col) if col in columnas else -1
                    d[col] = str(fila[idx]).strip() if idx >= 0 and idx < len(fila) else ""

            valido, error = ValidadorCheque.validar_fila(d, i)
            if not valido:
                self.errores.append((i, error))
                continue

            serie = d["serie"].upper()
            numero = int(d["numero"])
            fecha = d["fecha_emision"]
            beneficiario = d["beneficiario"].upper()
            importe = int(d["importe"].replace(".", "").replace(",", ""))
            importe_letras = numero_a_letras(importe)
            concepto = d.get("concepto", "").upper()

            if self.gestor_db.verificar_duplicado(serie, numero):
                self.duplicados.append((i, f"{serie}-{numero}"))
                continue

            self.datos.append({
                "fila": i,
                "serie": serie,
                "numero": numero,
                "fecha_emision": fecha,
                "beneficiario": beneficiario,
                "importe_num": importe,
                "importe_letras": importe_letras,
                "concepto": concepto,
                "plantilla": "",
            })

        total = len(self.datos) + len(self.errores) + len(self.duplicados)
        if total == 0:
            return False, "El archivo no contiene datos validos"

        return True, ""

    def importar(self) -> Dict:
        """Importa todos los datos validados a la base de datos."""
        insertados = 0
        fallados = 0

        for cheque in self.datos:
            if self.gestor_db.insertar_cheque(
                cheque["serie"],
                cheque["numero"],
                cheque["fecha_emision"],
                cheque["beneficiario"],
                cheque["importe_num"],
                cheque["importe_letras"],
                cheque["concepto"],
                cheque["plantilla"],
            ):
                insertados += 1
            else:
                fallados += 1

        return {
            "insertados": insertados,
            "fallados": fallados,
            "total_en_archivo": len(self.datos) + len(self.errores) + len(self.duplicados),
            "validos": len(self.datos),
            "errores_validacion": len(self.errores),
            "duplicados": len(self.duplicados),
        }


class VentanaCargaMasiva:
    """Ventana para carga masiva de cheques desde archivo."""

    def __init__(self, ventana_padre, gestor_db: GestionadorCheques):
        self.gestor_db = gestor_db
        self.carga = CargaMasiva(gestor_db)
        self.ruta_archivo = None

        self.ventana = tk.Toplevel(ventana_padre)
        self.ventana.title("Carga Masiva de Cheques")
        self.ventana.geometry("780x600")
        self.ventana.resizable(False, False)

        self.ventana.grab_set()
        self.ventana.transient(ventana_padre)

        bg = "#f5f5f5"
        self.ventana.configure(bg=bg)

        self._crear_interfaz()

        self.ventana.update_idletasks()
        x = ventana_padre.winfo_x() + (ventana_padre.winfo_width() // 2) - (self.ventana.winfo_width() // 2)
        y = ventana_padre.winfo_y() + (ventana_padre.winfo_height() // 2) - (self.ventana.winfo_height() // 2)
        self.ventana.geometry(f"+{x}+{y}")

    def _crear_interfaz(self):
        bg = "#f5f5f5"

        style = ttk.Style()
        style.configure("Importar.TButton", font=("Segoe UI", 10, "bold"))

        tk.Label(self.ventana, text="Carga Masiva de Cheques",
                 font=("Segoe UI", 14, "bold"), bg=bg,
                 fg="#202124").pack(anchor=tk.W, padx=20, pady=(15, 2))

        tk.Label(self.ventana,
                 text="Importa multiples cheques desde un archivo CSV (.csv) o Excel (.xlsx)",
                 font=("Segoe UI", 9), bg=bg,
                 fg="#5f6368").pack(anchor=tk.W, padx=20, pady=(0, 10))

        ttk.Separator(self.ventana, orient="horizontal").pack(fill=tk.X, padx=20, pady=(0, 10))

        frame_seleccion = tk.Frame(self.ventana, bg=bg)
        frame_seleccion.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(frame_seleccion, text="Archivo:", font=("Segoe UI", 10, "bold"),
                 bg=bg).pack(side=tk.LEFT)

        self.lbl_ruta = tk.Label(frame_seleccion, text="Ningun archivo seleccionado",
                                 font=("Segoe UI", 9), bg="#ffffff", fg="#5f6368",
                                 anchor=tk.W, padx=8, pady=4,
                                 relief=tk.SUNKEN, bd=1)
        self.lbl_ruta.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        btn_examinar = tk.Button(frame_seleccion, text="Examinar...",
                                 font=("Segoe UI", 9), bg="#e8f0fe",
                                 command=self._seleccionar_archivo,
                                 padx=12, pady=2)
        btn_examinar.pack(side=tk.LEFT)

        frame_info = tk.Frame(self.ventana, bg="#ffffff", bd=1, relief=tk.SUNKEN)
        frame_info.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.lbl_info = tk.Label(frame_info,
                                 text="Selecciona un archivo CSV o Excel para comenzar",
                                 font=("Segoe UI", 9), bg="#ffffff",
                                 fg="#5f6368", anchor=tk.W,
                                 padx=10, pady=8)
        self.lbl_info.pack(fill=tk.X)

        frame_tabla = tk.LabelFrame(self.ventana, text=" Vista Previa ",
                                    font=("Segoe UI", 10, "bold"),
                                    bg=bg, padx=8, pady=8)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        contenedor_tabla = tk.Frame(frame_tabla, bg=bg)
        contenedor_tabla.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(contenedor_tabla)
        scroll_x = ttk.Scrollbar(contenedor_tabla, orient=tk.HORIZONTAL)

        self.tree = ttk.Treeview(
            contenedor_tabla,
            columns=("fila", "serie", "numero", "fecha", "beneficiario", "importe", "estado"),
            height=8,
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("fila", width=40, anchor=tk.CENTER)
        self.tree.column("serie", width=60, anchor=tk.CENTER)
        self.tree.column("numero", width=70, anchor=tk.CENTER)
        self.tree.column("fecha", width=70, anchor=tk.CENTER)
        self.tree.column("beneficiario", width=180, anchor=tk.W)
        self.tree.column("importe", width=100, anchor=tk.E)
        self.tree.column("estado", width=100, anchor=tk.CENTER)

        self.tree.heading("#0", text="")
        self.tree.heading("fila", text="#")
        self.tree.heading("serie", text="Serie")
        self.tree.heading("numero", text="Numero")
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("beneficiario", text="Beneficiario")
        self.tree.heading("importe", text="Importe")
        self.tree.heading("estado", text="Estado")

        self.tree.tag_configure("valido", foreground="#1b8a3d")
        self.tree.tag_configure("error", foreground="#d93025")
        self.tree.tag_configure("duplicado", foreground="#e8711a")

        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        scroll_x.grid(row=1, column=0, sticky=tk.EW)

        contenedor_tabla.grid_rowconfigure(0, weight=1)
        contenedor_tabla.grid_columnconfigure(0, weight=1)

        frame_resumen = tk.Frame(self.ventana, bg=bg)
        frame_resumen.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.lbl_resumen = tk.Label(frame_resumen, text="",
                                    font=("Segoe UI", 9), bg=bg, fg="#5f6368")
        self.lbl_resumen.pack(side=tk.LEFT)

        frame_acciones = tk.Frame(self.ventana, bg=bg)
        frame_acciones.pack(fill=tk.X, padx=20, pady=(0, 15))

        btn_formato = tk.Button(frame_acciones, text="Ver Formato Esperado",
                                font=("Segoe UI", 9),
                                bg="#f1f3f4", command=self._mostrar_formato,
                                padx=10, pady=4)
        btn_formato.pack(side=tk.LEFT, padx=3)

        self.btn_importar = ttk.Button(frame_acciones, text="Importar Cheques",
                                       style="Importar.TButton",
                                       state=tk.DISABLED,
                                       command=self._importar)
        self.btn_importar.pack(side=tk.RIGHT, padx=3)

        btn_cerrar = tk.Button(frame_acciones, text="Cerrar",
                               font=("Segoe UI", 10),
                               bg="#f1f3f4", command=self.ventana.destroy,
                               padx=15, pady=6)
        btn_cerrar.pack(side=tk.RIGHT, padx=3)

    def _seleccionar_archivo(self):
        tipos = [
            ("Archivos compatibles", "*.csv *.xlsx"),
            ("CSV", "*.csv"),
        ]
        if TIENE_OPENPYXL:
            tipos.insert(1, ("Excel", "*.xlsx"))

        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de cheques",
            filetypes=tipos,
        )
        if not ruta:
            return

        self.ruta_archivo = ruta
        self.lbl_ruta.config(text=ruta)
        self._cargar_archivo()

    def _cargar_archivo(self):
        self.tree.delete(*self.tree.get_children())
        self.btn_importar.config(state=tk.DISABLED)
        self.lbl_resumen.config(text="")

        ext = Path(self.ruta_archivo).suffix.lower()

        if ext == ".csv":
            ok, msg = self.carga.leer_csv(self.ruta_archivo)
        elif ext == ".xlsx":
            ok, msg = self.carga.leer_excel(self.ruta_archivo)
        else:
            self.lbl_info.config(text="Formato no soportado. Usa .csv o .xlsx",
                                 fg="#d93025")
            return

        if not ok and not self.carga.datos and not self.carga.errores and not self.carga.duplicados:
            self.lbl_info.config(text=f"Error: {msg}", fg="#d93025")
            return

        if not ok and msg:
            self.lbl_info.config(text=msg, fg="#e8711a")
        else:
            self.lbl_info.config(text="Archivo cargado correctamente", fg="#1b8a3d")

        for d in self.carga.datos:
            imp_fmt = f"{d['importe_num']:,}".replace(",", ".")
            self.tree.insert("", tk.END,
                             values=(d.get("fila", "-"), d["serie"], d["numero"],
                                     d["fecha_emision"], d["beneficiario"],
                                     imp_fmt, "Valido"),
                             tags=("valido",))

        for fila, error in self.carga.errores:
            self.tree.insert("", tk.END,
                             values=(fila, "-", "-", "-", "-", "-", "Error"),
                             tags=("error",))

        for fila, ref in self.carga.duplicados:
            self.tree.insert("", tk.END,
                             values=(fila, ref.split("-")[0], ref.split("-")[1],
                                     "-", "-", "-", "Duplicado"),
                             tags=("duplicado",))

        total = len(self.carga.datos) + len(self.carga.errores) + len(self.carga.duplicados)
        resumen = f"Total: {total} filas  |  "
        resumen += f"Validas: {len(self.carga.datos)}  |  "
        resumen += f"Errores: {len(self.carga.errores)}  |  "
        resumen += f"Duplicados: {len(self.carga.duplicados)}"
        self.lbl_resumen.config(text=resumen)

        if self.carga.datos:
            self.btn_importar.config(state=tk.NORMAL,
                                     text=f"Importar {len(self.carga.datos)} Cheques")
        else:
            self.btn_importar.config(state=tk.DISABLED, text="Importar Cheques")

    def _importar(self):
        if not self.carga.datos:
            messagebox.showwarning("Sin datos", "No hay cheques validos para importar")
            return

        n = len(self.carga.datos)
        if not messagebox.askyesno(
            "Confirmar Importacion",
            f"Se importaran {n} cheque(s) a la base de datos.\n"
            f"Los que tengan errores o esten duplicados seran omitidos.\n\n"
            f"Confirmar importacion?"
        ):
            return

        self.btn_importar.config(state=tk.DISABLED, text="Importando...")
        self.ventana.update()

        resultado = self.carga.importar()

        messagebox.showinfo(
            "Importacion Completada",
            f"Resultado de la importacion:\n\n"
            f"  Insertados: {resultado['insertados']}\n"
            f"  Omitidos (error validacion): {resultado['errores_validacion']}\n"
            f"  Omitidos (duplicados): {resultado['duplicados']}\n"
            f"  Fallados: {resultado['fallados']}\n\n"
            f"Total en archivo: {resultado['total_en_archivo']} filas"
        )

        self.ventana.destroy()

    def _mostrar_formato(self):
        messagebox.showinfo(
            "Formato Esperado",
            "El archivo debe tener las siguientes columnas en la primera fila:\n\n"
            "  serie, numero, fecha_emision, beneficiario, importe, concepto\n\n"
            "Ejemplo:\n"
            "  serie,numero,fecha_emision,beneficiario,importe,concepto\n"
            "  CD,1001,15/05,Juan Perez,125000,Pago servicios\n"
            "  AB,1002,16/05,Maria Garcia,50000,\n\n"
            "Tambien soporta punto y coma (;) como separador.\n"
            "Para Excel (.xlsx), usa las mismas columnas en la primera fila.\n\n"
            "El importe es en guaraniess (enteros, sin decimales).\n"
            "La fecha debe ser en formato dd/mm."
        )
