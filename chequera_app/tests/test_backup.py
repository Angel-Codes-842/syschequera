"""
Tests unitarios para el módulo backup.py
"""

import unittest
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backup import GestorBackup


class TestGestorBackup(unittest.TestCase):
    """Tests para el gestor de backups."""
    
    def setUp(self):
        """Configuración antes de cada test."""
        self.bd_test = "test_backup_unit.db"
        self.backup_dir = "test_backups_unit"
        
        # Crear BD de prueba
        conn = sqlite3.connect(self.bd_test)
        conn.execute("CREATE TABLE test (id INTEGER, nombre TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'prueba')")
        conn.commit()
        conn.close()
        
        # Crear gestor
        self.gestor = GestorBackup(self.bd_test, self.backup_dir, max_backups=3)
    
    def tearDown(self):
        """Limpieza después de cada test."""
        if os.path.exists(self.bd_test):
            os.remove(self.bd_test)
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)
    
    def test_creacion_backup(self):
        """Test que se crea un backup correctamente."""
        ruta_backup = self.gestor.crear_backup()
        
        self.assertIsNotNone(ruta_backup)
        self.assertTrue(os.path.exists(ruta_backup))
        self.assertTrue(ruta_backup.endswith(".db"))
    
    def test_limite_backups(self):
        """Test que se respeta el límite de backups."""
        # Crear 5 backups (límite es 3) con delays para timestamps distintos
        for _ in range(5):
            self.gestor.crear_backup()
            time.sleep(0.1)  # Pequeño delay para timestamps distintos
        
        backups = self.gestor.listar_backups()
        self.assertEqual(len(backups), 3, "Debería haber solo 3 backups")
    
    def test_listar_backups(self):
        """Test listar backups disponibles."""
        self.gestor.crear_backup()
        time.sleep(0.1)
        self.gestor.crear_backup()
        
        backups = self.gestor.listar_backups()
        self.assertEqual(len(backups), 2)
        self.assertTrue(all(b.endswith(".db") for b in backups))
    
    def test_restaurar_backup(self):
        """Test restaurar un backup."""
        # Crear backup
        ruta_backup = self.gestor.crear_backup()
        
        # Modificar BD original
        conn = sqlite3.connect(self.bd_test)
        conn.execute("INSERT INTO test VALUES (2, 'modificado')")
        conn.commit()
        conn.close()
        
        # Verificar que tiene 2 registros
        conn = sqlite3.connect(self.bd_test)
        count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
        conn.close()
        self.assertEqual(count, 2)
        
        # Restaurar backup
        resultado = self.gestor.restaurar_backup(ruta_backup)
        self.assertTrue(resultado)
        
        # Verificar que volvió a tener 1 registro
        conn = sqlite3.connect(self.bd_test)
        count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)
    
    def test_backup_bd_inexistente(self):
        """Test backup con BD inexistente."""
        gestor = GestorBackup("no_existe.db", self.backup_dir)
        resultado = gestor.crear_backup()
        self.assertIsNone(resultado)


if __name__ == "__main__":
    unittest.main()
