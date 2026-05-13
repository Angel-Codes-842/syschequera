"""
Tests unitarios para el módulo num2letras.py
"""

import unittest
import sys
from pathlib import Path

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from num2letras import numero_a_letras


class TestNum2Letras(unittest.TestCase):
    """Tests para conversión de números a letras."""
    
    def test_cero(self):
        """Test conversión de cero."""
        resultado = numero_a_letras(0)
        self.assertEqual(resultado, "CERO GUARANÍES")
    
    def test_unidades(self):
        """Test conversión de unidades (1-9)."""
        self.assertEqual(numero_a_letras(1), "UN GUARANÍ")
        self.assertEqual(numero_a_letras(5), "CINCO GUARANÍES")
        self.assertEqual(numero_a_letras(9), "NUEVE GUARANÍES")
    
    def test_decenas_especiales(self):
        """Test decenas especiales (10-19, 21-29)."""
        self.assertEqual(numero_a_letras(10), "DIEZ GUARANÍES")
        self.assertEqual(numero_a_letras(15), "QUINCE GUARANÍES")
        self.assertEqual(numero_a_letras(20), "VEINTE GUARANÍES")
        self.assertEqual(numero_a_letras(21), "VEINTIUNO GUARANÍES")
        self.assertEqual(numero_a_letras(29), "VEINTINUEVE GUARANÍES")
    
    def test_decenas_comunes(self):
        """Test decenas comunes (30-90)."""
        self.assertEqual(numero_a_letras(30), "TREINTA GUARANÍES")
        self.assertEqual(numero_a_letras(45), "CUARENTA Y CINCO GUARANÍES")
        self.assertEqual(numero_a_letras(99), "NOVENTA Y NUEVE GUARANÍES")
    
    def test_centenas(self):
        """Test centenas."""
        self.assertEqual(numero_a_letras(100), "CIEN GUARANÍES")
        self.assertEqual(numero_a_letras(101), "CIENTO UNO GUARANÍES")
        self.assertEqual(numero_a_letras(250), "DOSCIENTOS CINCUENTA GUARANÍES")
        self.assertEqual(numero_a_letras(999), "NOVECIENTOS NOVENTA Y NUEVE GUARANÍES")
    
    def test_miles(self):
        """Test miles."""
        self.assertEqual(numero_a_letras(1000), "MIL GUARANÍES")
        self.assertEqual(numero_a_letras(1001), "MIL UNO GUARANÍES")
        self.assertEqual(numero_a_letras(125000), "CIENTO VEINTICINCO MIL GUARANÍES")
        self.assertEqual(numero_a_letras(999999), "NOVECIENTOS NOVENTA Y NUEVE MIL NOVECIENTOS NOVENTA Y NUEVE GUARANÍES")
    
    def test_millones(self):
        """Test millones."""
        self.assertEqual(numero_a_letras(1000000), "UN MILLÓN DE GUARANÍES")
        self.assertEqual(numero_a_letras(2000000), "DOS MILLONES DE GUARANÍES")
        self.assertEqual(numero_a_letras(1250000), "UN MILLÓN DOSCIENTOS CINCUENTA MIL GUARANÍES")
    
    def test_mil_millones(self):
        """Test mil millones."""
        self.assertEqual(numero_a_letras(1000000000), "UN MIL MILLONES DE GUARANÍES")
        self.assertEqual(numero_a_letras(2000000000), "DOS MIL MILLONES DE GUARANÍES")
    
    def test_limite_superior(self):
        """Test límite superior (9,999,999,999)."""
        resultado = numero_a_letras(9999999999)
        self.assertIn("GUARANÍES", resultado)
        self.assertIn("NUEVE MIL", resultado)
    
    def test_fuera_de_rango_negativo(self):
        """Test número negativo (debe lanzar ValueError)."""
        with self.assertRaises(ValueError):
            numero_a_letras(-1)
    
    def test_fuera_de_rango_excesivo(self):
        """Test número excesivo (debe lanzar ValueError)."""
        with self.assertRaises(ValueError):
            numero_a_letras(10000000000)


if __name__ == "__main__":
    unittest.main()
