"""
Gestor de Configuración para Lucy AI
===================================

Maneja la carga, validación y acceso a la configuración del sistema.
Soporte para configuración por defecto, archivos JSON y variables de entorno.
Implementa sistema de configuración dinámico con recarga en tiempo real.
"""

import json
import os
import time
import logging
import threading
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from datetime import datetime
from core.logging_system import get_logger

class ConfigWatcher:
    """Observador de cambios en archivos de configuración"""
    
    def __init__(self, config_path: Path, callback: Callable[[], None], check_interval: int = 5):
        """
        Inicializa el observador de configuración
        
        Args:
            config_path: Ruta al archivo de configuración a observar
            callback: Función a llamar cuando se detecte un cambio
            check_interval: Intervalo de verificación en segundos
        """
        self.config_path = config_path
        self.callback = callback
        self.check_interval = check_interval
        self.last_modified = self._get_last_modified()
        self.running = False
        self.thread = None
        self.logger = get_logger(__name__)
        
    def _get_last_modified(self) -> float:
        """Obtiene la última fecha de modificación del archivo"""
        if self.config_path.exists():
            return self.config_path.stat().st_mtime
        return 0
        
    def _check_for_changes(self):
        """Verifica si hay cambios en el archivo de configuración"""
        while self.running:
            try:
                current_mtime = self._get_last_modified()
                if current_mtime > self.last_modified:
                    self.logger.info(f"Cambio detectado en {self.config_path}")
                    self.last_modified = current_mtime
                    self.callback()
            except Exception as e:
                self.logger.error(f"Error al verificar cambios: {e}")
            
            time.sleep(self.check_interval)
            
    def start(self):
        """Inicia el observador en un hilo separado"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._check_for_changes, daemon=True)
        self.thread.start()
        self.logger.info(f"Observador iniciado para {self.config_path}")
        
    def stop(self):
        """Detiene el observador"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        self.logger.info(f"Observador detenido para {self.config_path}")

class ConfigManager:
    """Gestor centralizado de configuración con soporte para recarga dinámica"""
    
    def __init__(self, config_path: Optional[str] = None, auto_reload: bool = True):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_path: Ruta al archivo de configuración. Si es None, usa el default.
            auto_reload: Si debe observar cambios en el archivo y recargar automáticamente
        """
        self.logger = get_logger(__name__)
        self._observers = []
        self._lock = threading.RLock()
        
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
        
        # Iniciar observador si está habilitado
        if auto_reload:
            self.watcher = ConfigWatcher(self.config_path, self.reload_config)
            self.watcher.start()
    
    def register_observer(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Registra una función para ser notificada cuando cambie la configuración
        
        Args:
            callback: Función a llamar con la nueva configuración
        """
        with self._lock:
            self._observers.append(callback)
            
    def unregister_observer(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Elimina una función de la lista de observadores
        
        Args:
            callback: Función a eliminar
        """
        with self._lock:
            if callback in self._observers:
                self._observers.remove(callback)
                
    def reload_config(self) -> None:
        """Recarga la configuración desde el archivo"""
        with self._lock:
            old_config = self.config.copy()
            self.config = self._load_config()
            
            # Notificar a los observadores
            for observer in self._observers:
                try:
                    observer(self.config)
                except Exception as e:
                    self.logger.error(f"Error al notificar observador: {e}")
                    
            self.logger.info("Configuración recargada correctamente")
            
            # Registrar cambios
            changes = self._detect_changes(old_config, self.config)
            if changes:
                self.logger.info(f"Cambios detectados: {changes}")
                
    def _detect_changes(self, old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta cambios entre dos configuraciones
        
        Args:
            old_config: Configuración anterior
            new_config: Nueva configuración
            
        Returns:
            Diccionario con los cambios detectados
        """
        changes = {}
        
        def compare_dict(path, dict1, dict2):
            for key in set(list(dict1.keys()) + list(dict2.keys())):
                current_path = f"{path}.{key}" if path else key
                
                # Verificar si la clave existe en ambos
                if key not in dict1:
                    changes[current_path] = {"action": "added", "value": dict2[key]}
                elif key not in dict2:
                    changes[current_path] = {"action": "removed", "value": dict1[key]}
                else:
                    # Comparar valores
                    if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                        compare_dict(current_path, dict1[key], dict2[key])
                    elif dict1[key] != dict2[key]:
                        changes[current_path] = {
                            "action": "modified",
                            "old_value": dict1[key],
                            "new_value": dict2[key]
                        }
        
        compare_dict("", old_config, new_config)
        return changes
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