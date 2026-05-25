"""
Módulo de monitoreo básico del sistema.
Proporciona health checks y verificaciones de estado.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import sqlite3


class HealthCheck:
    """Realiza verificaciones de salud del sistema."""
    
    def __init__(self, ruta_bd: str = None, dir_base: str = None):
        """
        Inicializa el gestor de health checks.
        
        Args:
            ruta_bd: Ruta de la base de datos
            dir_base: Directorio base de la aplicación
        """
        self.dir_base = Path(dir_base) if dir_base else Path(__file__).parent
        self.ruta_bd = Path(ruta_bd) if ruta_bd else self.dir_base / "cheques.db"
        
        self.resultados: Dict[str, Tuple[bool, str]] = {}
    
    def verificar_bd(self) -> Tuple[bool, str]:
        """
        Verifica que la base de datos sea accesible.
        
        Returns:
            (estado, mensaje) donde estado es True si OK
        """
        try:
            if not self.ruta_bd.exists():
                return False, f"Base de datos no existe: {self.ruta_bd}"
            
            conn = sqlite3.connect(self.ruta_bd)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cheques")
                cursor.fetchone()
            finally:
                conn.close()
            
            return True, "Base de datos accesible"
            
        except sqlite3.OperationalError as e:
            return False, f"Error de base de datos: {e}"
        except Exception as e:
            return False, f"Error inesperado: {e}"
    
    def verificar_directorios(self) -> Tuple[bool, str]:
        """
        Verifica que los directorios necesarios existan.
        
        Returns:
            (estado, mensaje) donde estado es True si OK
        """
        directorios = [
            ("PDFs", self.dir_base / "PDFs"),
            ("plantillas", self.dir_base / "plantillas"),
            ("temp", self.dir_base / "temp"),
            ("backups", self.dir_base / "backups"),
        ]
        
        faltantes = []
        for nombre, ruta in directorios:
            if not ruta.exists():
                faltantes.append(nombre)
        
        if faltantes:
            return False, f"Directorios faltantes: {', '.join(faltantes)}"
        
        return True, "Todos los directorios existen"
    
    def verificar_dependencias(self) -> Tuple[bool, str]:
        """
        Verifica que las dependencias externas estén instaladas.
        
        Returns:
            (estado, mensaje) donde estado es True si OK
        """
        dependencias = [
            ("reportlab", "reportlab"),
            ("tkcalendar", "tkcalendar"),
        ]
        if sys.platform == "win32":
            dependencias.append(("win32print", "pywin32"))
        
        faltantes = []
        for modulo, nombre in dependencias:
            try:
                __import__(modulo)
            except ImportError:
                faltantes.append(nombre)
        
        if faltantes:
            return False, f"Dependencias faltantes: {', '.join(faltantes)}"
        
        return True, "Todas las dependencias instaladas"
    
    def verificar_config(self) -> Tuple[bool, str]:
        """
        Verifica que el archivo de configuración sea válido.
        
        Returns:
            (estado, mensaje) donde estado es True si OK
        """
        try:
            from config import obtener_config
            config = obtener_config(str(self.dir_base / "config.json"), str(self.dir_base))
            
            # Verificar valores críticos
            if not config.plantilla_actual:
                return False, "Configuración: plantilla_actual no definida"
            
            return True, "Configuración válida"
            
        except Exception as e:
            return False, f"Error en configuración: {e}"
    
    def verificar_backups(self) -> Tuple[bool, str]:
        """
        Verifica que el sistema de backups funcione.
        
        Returns:
            (estado, mensaje) donde estado es True si OK
        """
        try:
            from backup import GestorBackup
            
            gestor = GestorBackup(str(self.ruta_bd), max_backups=10)
            backup_dir = gestor.ruta_backups
            
            if not backup_dir.exists():
                return False, f"Directorio de backups no existe: {backup_dir}"
            
            return True, f"Sistema de backups OK (dir: {backup_dir})"
            
        except Exception as e:
            return False, f"Error en sistema de backups: {e}"
    
    def ejecutar_todos(self) -> Dict[str, Tuple[bool, str]]:
        """
        Ejecuta todas las verificaciones.
        
        Returns:
            Diccionario con resultados de cada check
        """
        self.resultados = {
            "base_de_datos": self.verificar_bd(),
            "directorios": self.verificar_directorios(),
            "dependencias": self.verificar_dependencias(),
            "configuracion": self.verificar_config(),
            "backups": self.verificar_backups(),
        }
        
        return self.resultados
    
    def obtener_estado_general(self) -> bool:
        """
        Obtiene el estado general del sistema.
        
        Returns:
            True si todos los checks pasan
        """
        if not self.resultados:
            self.ejecutar_todos()
        
        return all(estado for estado, _ in self.resultados.values())
    
    def reporte_consola(self):
        """Imprime un reporte de los health checks en consola."""
        print("=" * 80)
        print("HEALTH CHECK - Sistema de Cheques")
        print("=" * 80)
        
        if not self.resultados:
            self.ejecutar_todos()
        
        for nombre, (estado, mensaje) in self.resultados.items():
            icono = "✓" if estado else "✗"
            print(f"{icono} {nombre.replace('_', ' ').title()}: {mensaje}")
        
        print("=" * 80)
        estado_general = self.obtener_estado_general()
        print(f"Estado general: {'OK' if estado_general else 'ERROR'}")
        print("=" * 80)


def verificar_sistema(ruta_bd: str = None, dir_base: str = None) -> bool:
    """
    Función de conveniencia para verificar el sistema completo.
    
    Args:
        ruta_bd: Ruta de la base de datos
        dir_base: Directorio base de la aplicación
    
    Returns:
        True si el sistema está saludable
    """
    health = HealthCheck(ruta_bd, dir_base)
    health.reporte_consola()
    return health.obtener_estado_general()


if __name__ == "__main__":
    # Test del módulo
    print("Pruebas de monitoreo.py:")
    print("-" * 80)
    
    # Ejecutar health check
    resultado = verificar_sistema()
    
    print(f"\nResultado: {'SISTEMA SALUDABLE' if resultado else 'SISTEMA CON ERRORES'}")
    print("-" * 80)
