"""
Módulo centralizado de configuración.
Gestiona toda la configuración del sistema de forma unificada.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import os


class Config:
    """Gestor centralizado de configuración."""
    
    # Valores por defecto
    DEFAULT_CONFIG = {
        "offset_x": 0.0,
        "offset_y": 0.0,
        "plantilla_actual": "BNF",
        "ruta_plantillas": "plantillas",
        "ruta_pdfs": "PDFs",
        "ruta_bd": "cheques.db",
        "impresora_predeterminada": "Impresora Predeterminada",
        "tamaño_fuente_default": 11,
        "rotar_90": False,
        "max_backups": 10,
        "validar_fecha_futura_dias": 30,
        "max_longitud_serie": 10,
        "max_longitud_beneficiario": 100,
        "max_longitud_concepto": 200,
        "max_importe": 9999999999
    }
    
    def __init__(self, ruta_config: str = None, dir_base: str = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            ruta_config: Ruta del archivo config.json (default: dir_base/config.json)
            dir_base: Directorio base de la aplicación (default: directorio actual)
        """
        self.dir_base = Path(dir_base) if dir_base else Path(__file__).parent
        self.ruta_config = Path(ruta_config) if ruta_config else self.dir_base / "config.json"
        
        # Cargar configuración
        self._config = self._cargar_config()
    
    def _cargar_config(self) -> Dict[str, Any]:
        """
        Carga la configuración desde el archivo o usa valores por defecto.
        
        Returns:
            Diccionario con la configuración completa
        """
        config = self.DEFAULT_CONFIG.copy()
        
        if self.ruta_config.exists():
            try:
                with open(self.ruta_config, 'r', encoding='utf-8') as f:
                    config_usuario = json.load(f)
                # Fusionar con defaults (los valores del usuario sobrescriben)
                config.update(config_usuario)
            except (json.JSONDecodeError, OSError, IOError) as e:
                print(f"Advertencia: Error al cargar config.json, usando defaults: {e}")
        
        return config
    
    def guardar(self) -> bool:
        """
        Guarda la configuración actual en el archivo.
        
        Returns:
            True si se guardó correctamente, False si falló
        """
        try:
            # Crear directorio si no existe
            self.ruta_config.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.ruta_config, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, IOError, PermissionError) as e:
            print(f"Error al guardar configuración: {e}")
            return False
        except (TypeError, ValueError) as e:
            print(f"Error en datos de configuración: {e}")
            return False
    
    def obtener(self, clave: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            clave: Clave de configuración (puede ser anidada con puntos)
            default: Valor por defecto si no existe la clave
        
        Returns:
            Valor de configuración o default si no existe
        """
        # Soportar claves anidadas con puntos (ej: "plantilla.nombre")
        partes = clave.split(".")
        valor = self._config
        
        try:
            for parte in partes:
                valor = valor[parte]
            return valor
        except (KeyError, TypeError):
            return default
    
    def establecer(self, clave: str, valor: Any) -> bool:
        """
        Establece un valor de configuración.
        
        Args:
            clave: Clave de configuración (puede ser anidada con puntos)
            valor: Valor a establecer
        
        Returns:
            True si se estableció correctamente
        """
        try:
            # Soportar claves anidadas con puntos
            partes = clave.split(".")
            config = self._config
            
            # Navegar hasta el penúltimo nivel
            for parte in partes[:-1]:
                if parte not in config:
                    config[parte] = {}
                config = config[parte]
            
            # Establecer el valor en el último nivel
            config[partes[-1]] = valor
            return True
        except Exception as e:
            print(f"Error al establecer configuración {clave}: {e}")
            return False
    
    @property
    def offset_x(self) -> float:
        """Offset horizontal en mm."""
        return self._config.get("offset_x", 0.0)
    
    @offset_x.setter
    def offset_x(self, valor: float):
        self._config["offset_x"] = float(valor)
    
    @property
    def offset_y(self) -> float:
        """Offset vertical en mm."""
        return self._config.get("offset_y", 0.0)
    
    @offset_y.setter
    def offset_y(self, valor: float):
        self._config["offset_y"] = float(valor)
    
    @property
    def plantilla_actual(self) -> str:
        """Nombre de la plantilla actual."""
        return self._config.get("plantilla_actual", "BNF")
    
    @plantilla_actual.setter
    def plantilla_actual(self, valor: str):
        self._config["plantilla_actual"] = str(valor)
    
    @property
    def rotar_90(self) -> bool:
        """Si se debe rotar el PDF 90 grados (Alimentación vertical)."""
        return self._config.get("rotar_90", False)
    
    @rotar_90.setter
    def rotar_90(self, valor: bool):
        self._config["rotar_90"] = bool(valor)
    
    @property
    def ruta_plantillas(self) -> Path:
        """Ruta de la carpeta de plantillas."""
        return self.dir_base / self._config.get("ruta_plantillas", "plantillas")
    
    @property
    def ruta_pdfs(self) -> Path:
        """Ruta de la carpeta de PDFs."""
        return self.dir_base / self._config.get("ruta_pdfs", "PDFs")
    
    @property
    def ruta_bd(self) -> Path:
        """Ruta del archivo de base de datos."""
        return self.dir_base / self._config.get("ruta_bd", "cheques.db")
    
    @property
    def impresora_predeterminada(self) -> str:
        """Nombre de la impresora predeterminada."""
        return self._config.get("impresora_predeterminada", "Impresora Predeterminada")
    
    @impresora_predeterminada.setter
    def impresora_predeterminada(self, valor: str):
        self._config["impresora_predeterminada"] = str(valor)
    
    @property
    def tamano_fuente(self) -> int:
        """Tamaño de fuente predeterminado."""
        return self._config.get("tamaño_fuente_default", 11)
    
    @tamano_fuente.setter
    def tamano_fuente(self, valor: int):
        self._config["tamaño_fuente_default"] = int(valor)
    
    @property
    def rotar(self) -> bool:
        """Si se debe rotar el PDF."""
        return self._config.get("rotar_90", False)
    
    @rotar.setter
    def rotar(self, valor: bool):
        self._config["rotar_90"] = bool(valor)
    
    @property
    def max_backups(self) -> int:
        """Número máximo de backups a conservar."""
        return self._config.get("max_backups", 10)
    
    @max_backups.setter
    def max_backups(self, valor: int):
        self._config["max_backups"] = int(valor)
    
    def a_dict(self) -> Dict[str, Any]:
        """
        Retorna la configuración completa como diccionario.
        
        Returns:
            Diccionario con toda la configuración
        """
        return self._config.copy()
    
    def __repr__(self) -> str:
        return f"Config(ruta={self.ruta_config}, dir_base={self.dir_base})"


# Instancia global de configuración
_config_global: Optional[Config] = None


def obtener_config(ruta_config: str = None, dir_base: str = None) -> Config:
    """
    Obtiene la instancia global de configuración (singleton).
    
    Args:
        ruta_config: Ruta del archivo config.json
        dir_base: Directorio base de la aplicación
    
    Returns:
        Instancia de Config
    """
    global _config_global
    if _config_global is None:
        _config_global = Config(ruta_config, dir_base)
    return _config_global


def reiniciar_config():
    """Reinicia la instancia global de configuración."""
    global _config_global
    _config_global = None


if __name__ == "__main__":
    # Test del módulo
    print("Pruebas de config.py:")
    print("-" * 80)
    
    # Crear config de prueba
    config = Config("test_config.json", ".")
    
    # Test obtener valores
    print(f"[1/5] Offset X: {config.offset_x}")
    print(f"[1/5] Offset Y: {config.offset_y}")
    print(f"[1/5] Plantilla: {config.plantilla_actual}")
    
    # Test establecer valores
    print("\n[2/5] Estableciendo nuevos valores...")
    config.offset_x = 1.5
    config.offset_y = -0.5
    config.plantilla_actual = "Test"
    print(f"  Offset X: {config.offset_x}")
    print(f"  Offset Y: {config.offset_y}")
    print(f"  Plantilla: {config.plantilla_actual}")
    
    # Test guardar
    print("\n[3/5] Guardando configuración...")
    resultado = config.guardar()
    print(f"  Resultado: {'OK' if resultado else 'FALLÓ'}")
    
    # Test cargar
    print("\n[4/5] Recargando configuración...")
    config2 = Config("test_config.json", ".")
    print(f"  Offset X cargado: {config2.offset_x}")
    print(f"  Offset Y cargado: {config2.offset_y}")
    
    # Test obtener con clave anidada
    print("\n[5/5] Probando obtener con clave anidada...")
    valor = config.obtener("offset_x", 999)
    print(f"  offset_x: {valor}")
    
    # Limpiar
    if os.path.exists("test_config.json"):
        os.remove("test_config.json")
    
    print("-" * 80)
    print("✓ Pruebas completadas")
