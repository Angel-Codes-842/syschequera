"""
Módulo de gestión de base de datos SQLite para historial de cheques.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from backup import GestorBackup
from migraciones import GestorMigraciones, inicializar_migraciones


class GestionadorCheques:
    """Gestiona la base de datos SQLite de cheques emitidos."""
    
    def __init__(self, ruta_bd: str = "cheques.db"):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            ruta_bd: Ruta del archivo SQLite (default: cheques.db en el directorio actual)
        """
        self.ruta_bd = ruta_bd
        self.gestor_backup = GestorBackup(ruta_bd, max_backups=10)
        self.crear_tabla()
        
        # Inicializar y aplicar migraciones pendientes
        self.gestor_migraciones = GestorMigraciones(ruta_bd)
        self.gestor_migraciones.migrar()
    
    def _conectar(self) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos."""
        conn = sqlite3.connect(self.ruta_bd)
        conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
        return conn
    
    def _agregar_columna_plantilla(self, cursor: sqlite3.Cursor) -> None:
        """Agrega la columna plantilla si no existe en la tabla cheques."""
        cursor.execute("PRAGMA table_info(cheques)")
        columnas = [fila[1] for fila in cursor.fetchall()]
        if "plantilla" not in columnas:
            cursor.execute("ALTER TABLE cheques ADD COLUMN plantilla TEXT DEFAULT ''")
    
    def crear_tabla(self) -> None:
        """Crea la tabla de cheques si no existe."""
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cheques (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serie TEXT NOT NULL,
                numero INTEGER NOT NULL,
                fecha_emision TEXT NOT NULL,
                beneficiario TEXT NOT NULL,
                importe_num INTEGER NOT NULL,
                importe_letras TEXT NOT NULL,
                concepto TEXT DEFAULT '',
                plantilla TEXT DEFAULT '',
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(serie, numero)
            )
        """)
        
        conn.commit()
        self._agregar_columna_plantilla(cursor)
        conn.commit()
        conn.close()
    
    def insertar_cheque(self, serie: str, numero: int, fecha_emision: str,
                       beneficiario: str, importe_num: int, importe_letras: str,
                       concepto: str = "", plantilla: str = "") -> bool:
        """
        Inserta un nuevo cheque en la base de datos.
        
        Args:
            serie: Serie del cheque (ej: "CD")
            numero: Número del cheque
            fecha_emision: Fecha en formato "dd/mm"
            beneficiario: Nombre del beneficiario
            importe_num: Importe en números (enteros)
            importe_letras: Importe en letras
            concepto: Concepto/descripción (opcional)
            plantilla: Nombre de la plantilla usada para generar el cheque
        
        Returns:
            True si se insertó correctamente, False si hubo error (duplicado)
        """
        try:
            conn = self._conectar()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cheques (serie, numero, fecha_emision, beneficiario, 
                                     importe_num, importe_letras, concepto, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'activo')
            """, (serie, numero, fecha_emision, beneficiario, 
                  importe_num, importe_letras, concepto))
            
            conn.commit()
            conn.close()
            
            # Crear backup automático después de insertar
            self.gestor_backup.crear_backup()
            
            return True
        
        except sqlite3.IntegrityError as e:
            print(f"Error: Cheque duplicado (serie={serie}, numero={numero}): {e}")
            return False
        except sqlite3.OperationalError as e:
            print(f"Error de base de datos al insertar: {e}")
            return False
        except (ValueError, TypeError) as e:
            print(f"Error en los datos proporcionados: {e}")
            return False
    
    def verificar_duplicado(self, serie: str, numero: int) -> bool:
        """
        Verifica si un cheque ya existe en la base de datos.
        
        Args:
            serie: Serie del cheque
            numero: Número del cheque
        
        Returns:
            True si ya existe, False si no existe
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cheques WHERE serie = ? AND numero = ?",
                      (serie, numero))
        resultado = cursor.fetchone()[0]
        conn.close()
        
        return resultado > 0
    
    def obtener_cheque(self, cheque_id: int) -> Optional[Dict]:
        """
        Obtiene un cheque específico por ID.
        
        Args:
            cheque_id: ID del cheque
        
        Returns:
            Diccionario con los datos del cheque o None si no existe
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cheques WHERE id = ?", (cheque_id,))
        fila = cursor.fetchone()
        conn.close()
        
        return dict(fila) if fila else None
    
    def obtener_historial_completo(self, limite: int = None) -> List[Dict]:
        """
        Obtiene todo el historial de cheques.
        
        Args:
            limite: Número máximo de registros a retornar
        
        Returns:
            Lista de diccionarios con los datos de cada cheque
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        if limite:
            cursor.execute("""
                SELECT * FROM cheques ORDER BY fecha_creacion DESC LIMIT ?
            """, (limite,))
        else:
            cursor.execute("SELECT * FROM cheques ORDER BY fecha_creacion DESC")
        
        filas = cursor.fetchall()
        conn.close()
        
        return [dict(fila) for fila in filas]
    
    def obtener_ultimos(self, limite: int = 50) -> List[Dict]:
        """
        Obtiene los últimos N cheques emitidos.
        
        Args:
            limite: Número de registros a retornar (default: 50)
        
        Returns:
            Lista de diccionarios con los datos de cada cheque
        """
        return self.obtener_historial_completo(limite)
    
    def filtrar_cheques(self, serie: str = None, numero_desde: int = None,
                       numero_hasta: int = None, fecha_desde: str = None,
                       fecha_hasta: str = None, beneficiario: str = None) -> List[Dict]:
        """
        Filtra cheques según criterios.
        
        Args:
            serie: Filtro por serie exacta
            numero_desde: Filtro por número mínimo
            numero_hasta: Filtro por número máximo
            fecha_desde: Filtro por fecha mínima (formato "dd/mm")
            fecha_hasta: Filtro por fecha máxima (formato "dd/mm")
            beneficiario: Filtro parcial por beneficiario
        
        Returns:
            Lista de diccionarios que coinciden con los criterios
        """
        query = "SELECT * FROM cheques WHERE 1=1"
        parametros = []
        
        if serie:
            query += " AND serie = ?"
            parametros.append(serie)
        
        if numero_desde is not None:
            query += " AND numero >= ?"
            parametros.append(numero_desde)
        
        if numero_hasta is not None:
            query += " AND numero <= ?"
            parametros.append(numero_hasta)
        
        if fecha_desde:
            query += " AND substr(fecha_emision, 4, 2) || substr(fecha_emision, 1, 2) >= ?"
            parametros.append(fecha_desde[3:5] + fecha_desde[0:2])
        
        if fecha_hasta:
            query += " AND substr(fecha_emision, 4, 2) || substr(fecha_emision, 1, 2) <= ?"
            parametros.append(fecha_hasta[3:5] + fecha_hasta[0:2])
        
        if beneficiario:
            query += " AND beneficiario LIKE ?"
            parametros.append(f"%{beneficiario}%")
        
        query += " ORDER BY fecha_creacion DESC"
        
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute(query, parametros)
        filas = cursor.fetchall()
        conn.close()
        
        return [dict(fila) for fila in filas]
    
    def eliminar_cheque(self, cheque_id: int) -> bool:
        """
        Elimina un cheque de la base de datos.
        
        Args:
            cheque_id: ID del cheque a eliminar
        
        Returns:
            True si se eliminó, False si no existe
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cheques WHERE id = ?", (cheque_id,))
        conn.commit()
        
        filas_afectadas = cursor.rowcount
        conn.close()
        
        return filas_afectadas > 0
    
    def anular_cheque(self, cheque_id: int, motivo: str = "") -> bool:
        """
        Anula un cheque (cambia estado a 'anulado').
        
        Args:
            cheque_id: ID del cheque a anular
            motivo: Motivo de la anulación (opcional)
        
        Returns:
            True si se anuló, False si no existe
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE cheques SET estado = 'anulado' WHERE id = ?",
            (cheque_id,)
        )
        conn.commit()
        
        filas_afectadas = cursor.rowcount
        conn.close()
        
        if filas_afectadas > 0:
            # Crear backup después de anular
            self.gestor_backup.crear_backup()
            return True
        return False
    
    def reactivar_cheque(self, cheque_id: int) -> bool:
        """
        Reactiva un cheque anulado (cambia estado a 'activo').
        
        Args:
            cheque_id: ID del cheque a reactivar
        
        Returns:
            True si se reactivó, False si no existe
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE cheques SET estado = 'activo' WHERE id = ?",
            (cheque_id,)
        )
        conn.commit()
        
        filas_afectadas = cursor.rowcount
        conn.close()
        
        if filas_afectadas > 0:
            # Crear backup después de reactivar
            self.gestor_backup.crear_backup()
            return True
        return False
    
    def obtener_estadisticas(self) -> Dict:
        """
        Obtiene estadísticas de la base de datos.
        
        Returns:
            Diccionario con total de cheques, importe total, etc.
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cheques")
        total_cheques = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(importe_num) FROM cheques")
        importe_total = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT DISTINCT serie FROM cheques")
        series = [fila[0] for fila in cursor.fetchall()]
        
        conn.close()
        
        return {
            "total_cheques": total_cheques,
            "importe_total": importe_total,
            "series": series
        }


if __name__ == "__main__":
    # Test del módulo
    print("Pruebas de db.py:")
    print("-" * 80)
    
    # Crear gestor con base de datos de prueba
    gestor = GestionadorCheques("test_cheques.db")
    
    # Limpiar previos
    if os.path.exists("test_cheques.db"):
        os.remove("test_cheques.db")
    
    gestor = GestionadorCheques("test_cheques.db")
    
    # Test 1: Insertar cheques
    print("✓ Test 1: Insertando cheques...")
    r1 = gestor.insertar_cheque("CD", 1001, "15/05", "Juan Pérez", 125000, "CIENTO VEINTICINCO MIL GUARANÍES", "Pago servicios")
    r2 = gestor.insertar_cheque("CD", 1002, "16/05", "María García", 50000, "CINCUENTA MIL GUARANÍES", "Factura")
    r3 = gestor.insertar_cheque("AB", 500, "17/05", "Carlos López", 250000, "DOSCIENTOS CINCUENTA MIL GUARANÍES", "")
    print(f"  Cheques insertados: {r1 and r2 and r3}")
    
    # Test 2: Verificar duplicado
    print("✓ Test 2: Verificando duplicado...")
    dup = gestor.verificar_duplicado("CD", 1001)
    print(f"  Cheque CD 1001 existe: {dup}")
    
    # Test 3: Obtener historial
    print("✓ Test 3: Obteniendo historial...")
    historial = gestor.obtener_historial_completo()
    print(f"  Total de cheques: {len(historial)}")
    
    # Test 4: Filtrar por serie
    print("✓ Test 4: Filtrando por serie CD...")
    cd_cheques = gestor.filtrar_cheques(serie="CD")
    print(f"  Cheques serie CD: {len(cd_cheques)}")
    
    # Test 5: Filtrar por rango de números
    print("✓ Test 5: Filtrando por rango de números...")
    rango = gestor.filtrar_cheques(numero_desde=1001, numero_hasta=1002)
    print(f"  Cheques en rango 1001-1002: {len(rango)}")
    
    # Test 6: Estadísticas
    print("✓ Test 6: Obteniendo estadísticas...")
    stats = gestor.obtener_estadisticas()
    print(f"  {stats}")
    
    # Limpiar
    os.remove("test_cheques.db")
    print("-" * 80)
    print("✓ Todos los tests completados correctamente")
