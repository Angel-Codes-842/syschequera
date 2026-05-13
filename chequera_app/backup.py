"""
Módulo de backup automático de base de datos.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import sqlite3


class GestorBackup:
    """Gestiona backups automáticos de la base de datos."""
    
    def __init__(self, ruta_bd: str, ruta_backups: str = None, max_backups: int = 10):
        """
        Inicializa el gestor de backups.
        
        Args:
            ruta_bd: Ruta del archivo de base de datos
            ruta_backups: Ruta de la carpeta de backups (default: ./backups)
            max_backups: Número máximo de backups a conservar
        """
        self.ruta_bd = Path(ruta_bd)
        self.ruta_backups = Path(ruta_backups) if ruta_backups else self.ruta_bd.parent / "backups"
        self.max_backups = max_backups
        
        # Crear carpeta de backups si no existe
        self.ruta_backups.mkdir(parents=True, exist_ok=True)
    
    def crear_backup(self) -> str:
        """
        Crea un backup de la base de datos.
        
        Returns:
            Ruta del backup creado o None si falla
        """
        if not self.ruta_bd.exists():
            print(f"Advertencia: Base de datos no encontrada en {self.ruta_bd}")
            return None
        
        try:
            # Generar nombre con timestamp incluyendo milisegundos para unicidad
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            nombre_backup = f"cheques_backup_{timestamp}.db"
            ruta_backup = self.ruta_backups / nombre_backup
            
            # Usar método seguro para SQLite (copiar archivo cerrado)
            # Primero verificar que no hay conexiones abiertas
            self._verificar_bd_cerrada()
            
            # Copiar archivo
            shutil.copy2(self.ruta_bd, ruta_backup)
            
            # Limpiar backups antiguos
            self._limpiar_backups_antiguos()
            
            print(f"Backup creado: {ruta_backup}")
            return str(ruta_backup)
            
        except (OSError, IOError, PermissionError) as e:
            print(f"Error de archivo al crear backup: {e}")
            return None
        except Exception as e:
            print(f"Error inesperado al crear backup: {e}")
            return None
    
    def _verificar_bd_cerrada(self):
        """Verifica que la base de datos no esté bloqueada."""
        try:
            conn = sqlite3.connect(self.ruta_bd)
            conn.close()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print("Advertencia: Base de datos bloqueada, intentando backup de todas formas...")
    
    def _limpiar_backups_antiguos(self):
        """Elimina los backups más antiguos si exceden el máximo."""
        backups = sorted(self.ruta_backups.glob("cheques_backup_*.db"))
        
        while len(backups) > self.max_backups:
            backup_mas_antiguo = backups.pop(0)
            backup_mas_antiguo.unlink()
            print(f"Backup antiguo eliminado: {backup_mas_antiguo.name}")
    
    def listar_backups(self) -> list:
        """
        Lista todos los backups disponibles.
        
        Returns:
            Lista de rutas de backups ordenadas por fecha (más reciente primero)
        """
        backups = sorted(self.ruta_backups.glob("cheques_backup_*.db"), reverse=True)
        return [str(b) for b in backups]
    
    def restaurar_backup(self, ruta_backup: str) -> bool:
        """
        Restaura un backup de la base de datos.
        
        Args:
            ruta_backup: Ruta del backup a restaurar
        
        Returns:
            True si se restauró correctamente, False si falla
        """
        ruta_backup = Path(ruta_backup)
        
        if not ruta_backup.exists():
            print(f"Error: Backup no encontrado en {ruta_backup}")
            return False
        
        try:
            # Crear backup del actual antes de restaurar
            if self.ruta_bd.exists():
                backup_pre_restauracion = self.ruta_bd.with_suffix(".db.pre_restore")
                shutil.copy2(self.ruta_bd, backup_pre_restauracion)
            
            # Restaurar
            shutil.copy2(ruta_backup, self.ruta_bd)
            print(f"Base de datos restaurada desde: {ruta_backup}")
            return True
            
        except (OSError, IOError, PermissionError) as e:
            print(f"Error de archivo al restaurar backup: {e}")
            return False
        except Exception as e:
            print(f"Error inesperado al restaurar backup: {e}")
            return False
    
    def backup_despues_de_cambio(self):
        """Crea un backup automáticamente después de un cambio importante."""
        self.crear_backup()


if __name__ == "__main__":
    # Test del módulo
    print("Pruebas de backup.py:")
    print("-" * 80)
    
    # Crear gestor con BD de prueba
    bd_test = "test_backup.db"
    if os.path.exists(bd_test):
        os.remove(bd_test)
    
    # Crear BD de prueba
    conn = sqlite3.connect(bd_test)
    conn.execute("CREATE TABLE test (id INTEGER, nombre TEXT)")
    conn.execute("INSERT INTO test VALUES (1, 'prueba')")
    conn.commit()
    conn.close()
    
    # Crear gestor
    gestor = GestorBackup(bd_test, "test_backups", max_backups=3)
    
    # Crear varios backups
    print("Creando backups...")
    for i in range(5):
        gestor.crear_backup()
    
    # Listar backups
    print("\nBackups disponibles:")
    for backup in gestor.listar_backups():
        print(f"  {backup}")
    
    # Verificar que solo hay 3
    backups = gestor.listar_backups()
    assert len(backups) == 3, f"Debería haber 3 backups, hay {len(backups)}"
    print(f"\n✓ Límite de backups respetado: {len(backups)}")
    
    # Limpiar
    shutil.rmtree("test_backups")
    os.remove(bd_test)
    
    print("-" * 80)
    print("✓ Pruebas completadas")
