"""
Sistema de migraciones de base de datos.
Permite versionar y aplicar cambios al esquema de forma controlada.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict
import json


class GestorMigraciones:
    """Gestiona migraciones del esquema de base de datos."""
    
    def __init__(self, ruta_bd: str):
        """
        Inicializa el gestor de migraciones.
        
        Args:
            ruta_bd: Ruta del archivo de base de datos
        """
        self.ruta_bd = Path(ruta_bd)
        self.ruta_migraciones = self.ruta_bd.parent / "migraciones"
        self.ruta_migraciones.mkdir(exist_ok=True)
        
        # Crear tabla de versiones si no existe
        self._crear_tabla_versiones()
    
    def _conectar(self) -> sqlite3.Connection:
        """Retorna una conexión a la base de datos."""
        conn = sqlite3.connect(self.ruta_bd)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _crear_tabla_versiones(self):
        """Crea la tabla de control de versiones de migraciones."""
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                fecha_aplicacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def obtener_version_actual(self) -> int:
        """
        Obtiene la versión actual del esquema.
        
        Returns:
            Número de versión actual (0 si no hay migraciones aplicadas)
        """
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        resultado = cursor.fetchone()[0]
        conn.close()
        
        return resultado if resultado else 0
    
    def listar_migraciones_pendientes(self) -> List[Dict]:
        """
        Lista las migraciones pendientes de aplicar.
        
        Returns:
            Lista de diccionarios con migraciones pendientes
        """
        version_actual = self.obtener_version_actual()
        migraciones = []
        
        # Buscar archivos de migración
        for archivo in sorted(self.ruta_migraciones.glob("*.sql")):
            # Extraer versión del nombre (formato: 001_descripcion.sql)
            try:
                version = int(archivo.stem.split("_")[0])
                if version > version_actual:
                    migraciones.append({
                        "version": version,
                        "nombre": archivo.stem,
                        "ruta": archivo
                    })
            except (ValueError, IndexError):
                continue
        
        return sorted(migraciones, key=lambda x: x["version"])
    
    def aplicar_migracion(self, ruta_sql: str) -> bool:
        """
        Aplica una migración desde un archivo SQL.
        
        Args:
            ruta_sql: Ruta del archivo SQL de migración
        
        Returns:
            True si se aplicó correctamente, False si falló
        """
        try:
            # Leer archivo SQL
            with open(ruta_sql, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # Extraer versión y nombre del archivo
            ruta = Path(ruta_sql)
            version = int(ruta.stem.split("_")[0])
            nombre = ruta.stem
            
            # Ejecutar SQL
            conn = self._conectar()
            cursor = conn.cursor()
            
            # Ejecutar cada statement separado por ;
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            
            # Registrar migración
            cursor.execute(
                "INSERT INTO schema_migrations (version, nombre) VALUES (?, ?)",
                (version, nombre)
            )
            
            conn.commit()
            conn.close()
            
            print(f"✓ Migración {version} aplicada: {nombre}")
            return True
            
        except sqlite3.OperationalError as e:
            print(f"✗ Error de base de datos en migración {ruta_sql}: {e}")
            return False
        except (OSError, IOError) as e:
            print(f"✗ Error al leer archivo de migración {ruta_sql}: {e}")
            return False
        except Exception as e:
            print(f"✗ Error inesperado al aplicar migración {ruta_sql}: {e}")
            return False
    
    def migrar(self) -> bool:
        """
        Aplica todas las migraciones pendientes.
        
        Returns:
            True si todas se aplicaron correctamente, False si alguna falló
        """
        pendientes = self.listar_migraciones_pendientes()
        
        if not pendientes:
            print("✓ Base de datos está actualizada (sin migraciones pendientes)")
            return True
        
        print(f"Aplicando {len(pendientes)} migración(es) pendiente(s)...")
        
        for migracion in pendientes:
            if not self.aplicar_migracion(migracion["ruta"]):
                return False
        
        print("✓ Todas las migraciones aplicadas correctamente")
        return True
    
    def crear_migracion(self, version: int, descripcion: str, sql: str):
        """
        Crea un nuevo archivo de migración.
        
        Args:
            version: Número de versión (debe ser único)
            descripcion: Descripción de la migración
            sql: SQL a ejecutar
        """
        nombre_archivo = f"{version:03d}_{descripcion.replace(' ', '_').lower()}.sql"
        ruta = self.ruta_migraciones / nombre_archivo
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(f"-- Migración {version}: {descripcion}\n")
            f.write(f"-- Generada automáticamente\n\n")
            f.write(sql)
        
        print(f"✓ Migración creada: {ruta}")


# Migraciones iniciales del sistema
MIGRACION_INICIAL = """
-- Agregar columna plantilla si no existe
-- Esta migración asegura compatibilidad con versiones anteriores
"""

MIGRACION_001 = """
-- Migración 001: Agregar índices para mejorar rendimiento

-- Índice en serie y numero para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_serie_numero ON cheques(serie, numero);

-- Índice en fecha de emisión
CREATE INDEX IF NOT EXISTS idx_fecha_emision ON cheques(fecha_emision);

-- Índice en beneficiario para búsquedas parciales
CREATE INDEX IF NOT EXISTS idx_beneficiario ON cheques(beneficiario);
"""


def inicializar_migraciones(ruta_bd: str):
    """
    Inicializa las migraciones del sistema creando los archivos necesarios.
    
    Args:
        ruta_bd: Ruta de la base de datos
    """
    gestor = GestorMigraciones(ruta_bd)
    
    # Crear migración inicial si no existe
    ruta_migracion = gestor.ruta_migraciones / "001_indices_rendimiento.sql"
    if not ruta_migracion.exists():
        gestor.crear_migracion(1, "indices_rendimiento", MIGRACION_001)
    
    print("Migraciones inicializadas")


if __name__ == "__main__":
    # Test del módulo
    import os
    import shutil
    
    print("Pruebas de migraciones.py:")
    print("-" * 80)
    
    # Crear BD de prueba
    bd_test = "test_migraciones.db"
    if os.path.exists(bd_test):
        os.remove(bd_test)
    
    # Inicializar migraciones
    inicializar_migraciones(bd_test)
    
    # Crear gestor
    gestor = GestorMigraciones(bd_test)
    
    # Verificar versión actual
    print(f"\n[1/4] Versión actual: {gestor.obtener_version_actual()}")
    
    # Listar pendientes
    print("\n[2/4] Migraciones pendientes:")
    pendientes = gestor.listar_migraciones_pendientes()
    for p in pendientes:
        print(f"  - {p['version']}: {p['nombre']}")
    
    # Aplicar migraciones
    print("\n[3/4] Aplicando migraciones...")
    resultado = gestor.migrar()
    print(f"  Resultado: {'OK' if resultado else 'FALLÓ'}")
    
    # Verificar versión después de migrar
    print(f"\n[4/4] Versión después de migrar: {gestor.obtener_version_actual()}")
    
    # Limpiar
    os.remove(bd_test)
    if os.path.exists("migraciones"):
        shutil.rmtree("migraciones")
    
    print("-" * 80)
    print("✓ Pruebas completadas")
