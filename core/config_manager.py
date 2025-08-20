"""
Gestor de Configuración para Lucy AI
===================================

Maneja la carga, validación y acceso a la configuración del sistema.
Soporte para configuración por defecto, archivos JSON y variables de entorno.
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Gestor centralizado de configuración"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_path: Ruta al archivo de configuración. Si es None, usa el default.
        """
        self.logger = logging.getLogger(__name__)
        
        # Rutas base
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        
        # Configuración por defecto
        self._default_config = self._get_default_config()
        
        # Cargar configuración
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self.config_dir / "config.json"
            
        self.config = self._load_config()
        self._validate_config()
        self._ensure_directories()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto como fallback"""
        return {
            "app": {
                "name": "Lucy AI",
                "version": "1.0.0"
            },
            "model": {
                "default_language": "es",
                "confidence_threshold": 0.25
            },
            "paths": {
                "data_dir": "data",
                "models_dir": "data/models",
                "intents_dir": "data/intents",
                "logs_dir": "logs"
            },
            "logging": {
                "level": "INFO",
                "file_enabled": True
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde archivo o usa default"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"Configuración cargada desde: {self.config_path}")
                
                # Merge con configuración default
                return self._merge_configs(self._default_config, config)
            else:
                self.logger.warning(f"Archivo de configuración no encontrado: {self.config_path}")
                self.logger.info("Usando configuración por defecto")
                return self._default_config.copy()
                
        except Exception as e:
            self.logger.error(f"Error cargando configuración: {e}")
            self.logger.info("Usando configuración por defecto")
            return self._default_config.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Combina configuración default con la del usuario"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _validate_config(self):
        """Valida la configuración cargada"""
        required_sections = ['app', 'model', 'paths', 'logging']
        
        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Sección requerida '{section}' no encontrada en configuración")
                raise ValueError(f"Configuración inválida: falta sección '{section}'")
        
        # Validaciones específicas
        if not isinstance(self.config['model']['confidence_threshold'], (int, float)):
            raise ValueError("confidence_threshold debe ser un número")
            
        if self.config['model']['confidence_threshold'] < 0 or self.config['model']['confidence_threshold'] > 1:
            raise ValueError("confidence_threshold debe estar entre 0 y 1")
    
    def _ensure_directories(self):
        """Crea directorios necesarios si no existen"""
        directories = [
            self.get_path('data_dir'),
            self.get_path('models_dir'),
            self.get_path('intents_dir'),
            self.get_path('logs_dir')
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando dot notation
        
        Args:
            key: Clave en formato 'seccion.subseccion.valor'
            default: Valor por defecto si no existe la clave
            
        Returns:
            Valor de configuración o default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        Establece un valor de configuración usando dot notation
        
        Args:
            key: Clave en formato 'seccion.subseccion.valor'
            value: Nuevo valor
        """
        keys = key.split('.')
        config_ref = self.config
        
        # Navegar hasta el penúltimo nivel
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        # Establecer valor final
        config_ref[keys[-1]] = value
        self.logger.info(f"Configuración actualizada: {key} = {value}")
    
    def get_path(self, path_key: str) -> str:
        """
        Obtiene una ruta absoluta basada en la configuración
        
        Args:
            path_key: Clave de la ruta en la sección 'paths'
            
        Returns:
            Ruta absoluta
        """
        relative_path = self.get(f'paths.{path_key}', '')
        if not relative_path:
            raise ValueError(f"Ruta '{path_key}' no configurada")
            
        return str(self.base_dir / relative_path)
    
    def save(self, path: Optional[str] = None):
        """
        Guarda la configuración actual en archivo
        
        Args:
            path: Ruta donde guardar. Si es None, usa la ruta actual.
        """
        save_path = Path(path) if path else self.config_path
        
        try:
            # Crear directorio si no existe
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Configuración guardada en: {save_path}")
            
        except Exception as e:
            self.logger.error(f"Error guardando configuración: {e}")
            raise
    
    def reload(self):
        """Recarga la configuración desde archivo"""
        self.config = self._load_config()
        self._validate_config()
        self._ensure_directories()
        self.logger.info("Configuración recargada")
    
    def get_all(self) -> Dict[str, Any]:
        """Retorna toda la configuración"""
        return self.config.copy()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """
        Verifica si una característica está habilitada
        
        Args:
            feature: Nombre de la característica
            
        Returns:
            True si está habilitada, False caso contrario
        """
        return self.get(f'features.{feature}', False)

# Instancia global para facilitar el acceso
_config_manager = None

def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Obtiene la instancia global del gestor de configuración"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    
    return _config_manager

def get_config(key: str, default: Any = None) -> Any:
    """Función de conveniencia para obtener configuración"""
    return get_config_manager().get(key, default)