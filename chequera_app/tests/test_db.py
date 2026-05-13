"""
Tests unitarios para el módulo db.py
"""

import unittest
import os
import sys
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import GestionadorCheques


class TestGestionadorCheques(unittest.TestCase):
    """Tests para el gestor de base de datos."""
    
    def setUp(self):
        """Configuración antes de cada test."""
        self.bd_test = "test_db_unit.db"
        if os.path.exists(self.bd_test):
            os.remove(self.bd_test)
        self.gestor = GestionadorCheques(self.bd_test)
    
    def tearDown(self):
        """Limpieza después de cada test."""
        # Forzar garbage collection y cerrar conexiones
        import gc
        gc.collect()
        
        # Intentar borrar el archivo con reintentos
        max_retries = 5
        for i in range(max_retries):
            try:
                if os.path.exists(self.bd_test):
                    os.remove(self.bd_test)
                break
            except PermissionError:
                if i < max_retries - 1:
                    import time
                    time.sleep(0.1)
                else:
                    # Si no se puede borrar, ignorar
                    pass
        
        # Limpiar backups
        backup_dir = Path(self.bd_test).parent / "backups"
        if backup_dir.exists():
            import shutil
            try:
                shutil.rmtree(backup_dir)
            except:
                pass
    
    def test_creacion_tabla(self):
        """Test que la tabla se crea correctamente."""
        conn = self.gestor._conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cheques'")
        tabla_existe = cursor.fetchone() is not None
        conn.close()
        self.assertTrue(tabla_existe)
    
    def test_insertar_cheque(self):
        """Test insertar un cheque."""
        resultado = self.gestor.insertar_cheque(
            "AB", 1001, "15/05", "Juan Pérez", 125000, 
            "CIENTO VEINTICINCO MIL GUARANÍES", "Test"
        )
        self.assertTrue(resultado)
    
    def test_insertar_cheque_duplicado(self):
        """Test que no permite cheques duplicados."""
        # Insertar primer cheque
        self.gestor.insertar_cheque(
            "AB", 1001, "15/05", "Juan Pérez", 125000, 
            "CIENTO VEINTICINCO MIL GUARANÍES", "Test"
        )
        
        # Intentar insertar duplicado
        resultado = self.gestor.insertar_cheque(
            "AB", 1001, "16/05", "Otro Nombre", 50000, 
            "CINCUENTA MIL GUARANÍES", "Test 2"
        )
        self.assertFalse(resultado, "No debería permitir cheques duplicados")
    
    def test_verificar_duplicado(self):
        """Test verificación de duplicados."""
        # Antes de insertar
        self.assertFalse(self.gestor.verificar_duplicado("AB", 1001))
        
        # Después de insertar
        self.gestor.insertar_cheque(
            "AB", 1001, "15/05", "Juan Pérez", 125000, 
            "CIENTO VEINTICINCO MIL GUARANÍES", "Test"
        )
        self.assertTrue(self.gestor.verificar_duplicado("AB", 1001))
    
    def test_obtener_cheque(self):
        """Test obtener un cheque específico."""
        # Insertar cheque
        self.gestor.insertar_cheque(
            "AB", 1001, "15/05", "Juan Pérez", 125000, 
            "CIENTO VEINTICINCO MIL GUARANÍES", "Test"
        )
        
        # Obtener cheque
        cheque = self.gestor.obtener_cheque(1)
        self.assertIsNotNone(cheque)
        self.assertEqual(cheque["serie"], "AB")
        self.assertEqual(cheque["numero"], 1001)
    
    def test_obtener_historial_completo(self):
        """Test obtener historial completo."""
        # Insertar varios cheques
        for i in range(5):
            self.gestor.insertar_cheque(
                "AB", 1000 + i, "15/05", f"Beneficiario {i}", 
                100000 * (i + 1), f"LETRAS {i}", f"Concepto {i}"
            )
        
        historial = self.gestor.obtener_historial_completo()
        self.assertEqual(len(historial), 5)
    
    def test_obtener_ultimos_con_limite(self):
        """Test obtener últimos N cheques."""
        # Insertar 10 cheques
        for i in range(10):
            self.gestor.insertar_cheque(
                "AB", 1000 + i, "15/05", f"Beneficiario {i}", 
                100000 * (i + 1), f"LETRAS {i}", f"Concepto {i}"
            )
        
        # Obtener solo los últimos 5
        ultimos = self.gestor.obtener_ultimos(5)
        self.assertEqual(len(ultimos), 5)
    
    def test_filtrar_por_serie(self):
        """Test filtrar por serie."""
        # Insertar cheques de diferentes series
        self.gestor.insertar_cheque("AB", 1001, "15/05", "Juan", 100000, "LETRAS", "Test")
        self.gestor.insertar_cheque("CD", 2001, "15/05", "Maria", 200000, "LETRAS", "Test")
        self.gestor.insertar_cheque("AB", 1002, "16/05", "Pedro", 150000, "LETRAS", "Test")
        
        filtrados = self.gestor.filtrar_cheques(serie="AB")
        self.assertEqual(len(filtrados), 2)
        self.assertTrue(all(c["serie"] == "AB" for c in filtrados))
    
    def test_filtrar_por_rango_numeros(self):
        """Test filtrar por rango de números."""
        # Insertar cheques
        for i in range(10):
            self.gestor.insertar_cheque("AB", 1000 + i, "15/05", f"Ben {i}", 100000, "LETRAS", "Test")
        
        # Filtrar rango 1003-1006
        filtrados = self.gestor.filtrar_cheques(numero_desde=1003, numero_hasta=1006)
        self.assertEqual(len(filtrados), 4)
    
    def test_filtrar_por_beneficiario(self):
        """Test filtrar por beneficiario (parcial)."""
        self.gestor.insertar_cheque("AB", 1001, "15/05", "Juan Pérez", 100000, "LETRAS", "Test")
        self.gestor.insertar_cheque("AB", 1002, "15/05", "Juan García", 200000, "LETRAS", "Test")
        self.gestor.insertar_cheque("AB", 1003, "15/05", "María López", 150000, "LETRAS", "Test")
        
        filtrados = self.gestor.filtrar_cheques(beneficiario="Juan")
        self.assertEqual(len(filtrados), 2)
    
    def test_eliminar_cheque(self):
        """Test eliminar un cheque."""
        # Insertar cheque
        self.gestor.insertar_cheque("AB", 1001, "15/05", "Juan", 100000, "LETRAS", "Test")
        
        # Verificar que existe
        self.assertTrue(self.gestor.verificar_duplicado("AB", 1001))
        
        # Eliminar
        resultado = self.gestor.eliminar_cheque(1)
        self.assertTrue(resultado)
        
        # Verificar que ya no existe
        self.assertFalse(self.gestor.verificar_duplicado("AB", 1001))
    
    def test_obtener_estadisticas(self):
        """Test obtener estadísticas."""
        # Insertar cheques
        self.gestor.insertar_cheque("AB", 1001, "15/05", "Juan", 100000, "LETRAS", "Test")
        self.gestor.insertar_cheque("CD", 2001, "15/05", "Maria", 200000, "LETRAS", "Test")
        
        stats = self.gestor.obtener_estadisticas()
        self.assertEqual(stats["total_cheques"], 2)
        self.assertEqual(stats["importe_total"], 300000)
        self.assertIn("AB", stats["series"])
        self.assertIn("CD", stats["series"])


if __name__ == "__main__":
    unittest.main()
