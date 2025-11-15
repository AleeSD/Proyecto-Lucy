"""
Sistema de Logging Avanzado para Lucy AI
========================================

Maneja múltiples niveles de logging, rotación de archivos,
formateo personalizado y envío de alertas.

Características:
- Logging estructurado en JSON
- Rotación automática de archivos
- Colores en consola
- Niveles personalizados
- Contexto de conversación
- Métricas de rendimiento
"""

import sys
import json
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

import colorlog
from pythonjsonlogger.json import JsonFormatter
from loguru import logger as loguru_logger
import yaml


class LogLevel(Enum):
    """Niveles de log personalizados para Lucy"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    ALERT = 60  # Nivel personalizado para alertas importantes


class LucyLogFormatter(logging.Formatter):
    """Formatter personalizado con contexto de Lucy"""
    
    def format(self, record):
        # Agregar contexto adicional
        if hasattr(record, 'session_id'):
            record.msg = f"[Session: {record.session_id}] {record.msg}"
        
        if hasattr(record, 'user_input'):
            record.msg = f"{record.msg} | Input: '{record.user_input[:50]}...'"
            
        if hasattr(record, 'response_time'):
            record.msg = f"{record.msg} | Time: {record.response_time:.2f}s"
            
        return super().format(record)


class ConversationLogger:
    """Logger especializado para conversaciones"""
    
    def __init__(self, log_dir: str = "logs/conversations"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Logger específico para conversaciones
        self.logger = logging.getLogger('lucy.conversations')
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para archivo JSON de conversaciones
        json_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'conversations.json',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        json_formatter = JsonFormatter(
            '%(timestamp)s %(session_id)s %(user_input)s %(bot_response)s '
            '%(intent)s %(confidence)s %(language)s %(response_time)s',
            timestamp=True
        )
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
        
    def log_conversation(self, session_id: str, user_input: str, 
                        bot_response: str, intent: str = None,
                        confidence: float = 0.0, language: str = 'es',
                        response_time: float = 0.0):
        """Registra una conversación completa"""
        self.logger.info(
            "Conversation",
            extra={
                'session_id': session_id,
                'user_input': user_input,
                'bot_response': bot_response,
                'intent': intent,
                'confidence': confidence,
                'language': language,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    def get_conversation_stats(self, session_id: str = None) -> Dict[str, Any]:
        """Obtiene estadísticas de conversaciones"""
        stats = {
            'total_conversations': 0,
            'average_confidence': 0.0,
            'average_response_time': 0.0,
            'languages': {},
            'top_intents': {}
        }
        
        # Leer archivo de conversaciones
        log_file = self.log_dir / 'conversations.json'
        if not log_file.exists():
            return stats
            
        conversations = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    conv = json.loads(line)
                    if session_id is None or conv.get('session_id') == session_id:
                        conversations.append(conv)
                except json.JSONDecodeError:
                    continue
        
        if not conversations:
            return stats
            
        # Calcular estadísticas
        stats['total_conversations'] = len(conversations)
        
        confidences = [c.get('confidence', 0) for c in conversations]
        stats['average_confidence'] = sum(confidences) / len(confidences) if confidences else 0
        
        response_times = [c.get('response_time', 0) for c in conversations]
        stats['average_response_time'] = sum(response_times) / len(response_times) if response_times else 0
        
        # Contar idiomas
        for conv in conversations:
            lang = conv.get('language', 'unknown')
            stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
        
        # Top intents
        for conv in conversations:
            intent = conv.get('intent', 'unknown')
            if intent:
                stats['top_intents'][intent] = stats['top_intents'].get(intent, 0) + 1
        
        # Ordenar top intents
        stats['top_intents'] = dict(sorted(
            stats['top_intents'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        return stats


class PerformanceLogger:
    """Logger para métricas de rendimiento"""
    
    def __init__(self, log_dir: str = "logs/performance"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('lucy.performance')
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para métricas de rendimiento
        perf_handler = logging.handlers.TimedRotatingFileHandler(
            self.log_dir / 'performance.log',
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        perf_formatter = JsonFormatter()
        perf_handler.setFormatter(perf_formatter)
        self.logger.addHandler(perf_handler)
        
        # Métricas en memoria para análisis rápido
        self.metrics_buffer = []
        self.max_buffer_size = 1000
        
    def log_metric(self, metric_name: str, value: float, 
                unit: str = None, tags: Dict[str, str] = None):
        """Registra una métrica de rendimiento"""
        metric_data = {
            'timestamp': datetime.now().isoformat(),
            'metric': metric_name,
            'value': value,
            'unit': unit,
            'tags': tags or {}
        }
        
        self.logger.info(f"Metric: {metric_name}", extra=metric_data)
        
        # Agregar al buffer
        self.metrics_buffer.append(metric_data)
        if len(self.metrics_buffer) > self.max_buffer_size:
            self.metrics_buffer.pop(0)
    
    def log_model_metrics(self, accuracy: float, loss: float, 
                        prediction_time: float, confidence: float):
        """Registra métricas específicas del modelo ML"""
        self.log_metric('model.accuracy', accuracy, 'percentage')
        self.log_metric('model.loss', loss, 'value')
        self.log_metric('model.prediction_time', prediction_time, 'seconds')
        self.log_metric('model.confidence', confidence, 'percentage')
    
    def get_recent_metrics(self, metric_name: str = None, 
                        last_n: int = 100) -> List[Dict[str, Any]]:
        """Obtiene métricas recientes del buffer"""
        if metric_name:
            return [m for m in self.metrics_buffer[-last_n:] 
                if m['metric'] == metric_name]
        return self.metrics_buffer[-last_n:]


class ErrorLogger:
    """Logger especializado para errores y excepciones"""
    
    def __init__(self, log_dir: str = "logs/errors"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('lucy.errors')
        self.logger.setLevel(logging.ERROR)
        
        # Handler para errores críticos
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'errors.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10,
            encoding='utf-8'
        )
        
        # Formato detallado para errores
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(funcName)s() - '
            '%(message)s\n'
            'Stack Trace:\n%(exc_info)s\n'
            '-' * 80
        )
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)
        
        # Contador de errores para alertas
        self.error_counts = {}
        self.alert_threshold = 10  # Alertar después de 10 errores similares
        
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                alert: bool = False):
        """Registra un error con contexto completo"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Contar errores similares
        error_key = f"{error_type}:{error_msg[:50]}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Preparar mensaje con contexto
        log_msg = f"Error: {error_type}: {error_msg}"
        if context:
            log_msg += f"\nContext: {json.dumps(context, indent=2)}"
        
        # Registrar error
        self.logger.error(log_msg, exc_info=True)
        
        # Verificar si necesita alerta
        if alert or self.error_counts[error_key] >= self.alert_threshold:
            self._send_alert(error_type, error_msg, context)
    
    def _send_alert(self, error_type: str, error_msg: str, 
                context: Dict[str, Any] = None):
        """Envía una alerta por error crítico"""
        # Por ahora solo loggeamos la alerta
        # En el futuro se puede integrar con Telegram, Slack, email, etc.
        alert_msg = f"🚨 ALERTA CRÍTICA: {error_type}\n{error_msg}"
        if context:
            alert_msg += f"\nContexto: {context}"
        
        self.logger.critical(alert_msg)
        print(f"\n{alert_msg}\n")  # También imprimir en consola


class LoggingManager:
    """Gestor central del sistema de logging"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
            
        self.initialized = True
        self.config = self._load_config()
        
        # Inicializar loggers especializados
        self.conversation_logger = ConversationLogger(
            self.config.get('conversation_log_dir', 'logs/conversations')
        )
        self.performance_logger = PerformanceLogger(
            self.config.get('performance_log_dir', 'logs/performance')
        )
        self.error_logger = ErrorLogger(
            self.config.get('error_log_dir', 'logs/errors')
        )
        
        # Configurar logger principal
        self._setup_main_logger()
        
        # Configurar Loguru para logging avanzado
        self._setup_loguru()
        
    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración de logging desde archivo YAML"""
        config_file = Path('config/logging.yaml')
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        
        # Configuración por defecto
        return {
            'log_level': 'INFO',
            'console_enabled': True,
            'file_enabled': True,
            'json_logging': True,
            'colored_output': True,
            'conversation_log_dir': 'logs/conversations',
            'performance_log_dir': 'logs/performance',
            'error_log_dir': 'logs/errors',
            'main_log_dir': 'logs'
        }
    
    def _setup_main_logger(self):
        """Configura el logger principal de Lucy"""
        # Logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.get('log_level', 'INFO')))
        
        # Limpiar handlers existentes
        root_logger.handlers.clear()
        
        # Handler de consola con colores
        if self.config.get('console_enabled', True):
            console_handler = logging.StreamHandler(sys.stdout)
            
            if self.config.get('colored_output', True):
                # Formato con colores
                console_formatter = colorlog.ColoredFormatter(
                    '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    log_colors={
                        'DEBUG': 'cyan',
                        'INFO': 'green',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'red,bg_white',
                    }
                )
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # Handler de archivo principal
        if self.config.get('file_enabled', True):
            log_dir = Path(self.config.get('main_log_dir', 'logs'))
            log_dir.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / 'lucy.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=10,
                encoding='utf-8'
            )
            
            if self.config.get('json_logging', True):
                file_formatter = JsonFormatter()
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - '
                    '%(filename)s:%(lineno)d - %(message)s'
                )
            
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
    
    def _setup_loguru(self):
        """Configura Loguru para logging avanzado"""
        # Remover configuración por defecto
        loguru_logger.remove()
        
        # Agregar consola con formato bonito
        if self.config.get('console_enabled', True):
            loguru_logger.add(
                sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                    "<level>{message}</level>",
                level=self.config.get('log_level', 'INFO')
            )
        
        # Agregar archivo con rotación
        if self.config.get('file_enabled', True):
            log_dir = Path(self.config.get('main_log_dir', 'logs'))
            loguru_logger.add(
                log_dir / 'lucy_detailed.log',
                rotation="10 MB",
                retention="30 days",
                compression="zip",
                level="DEBUG",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
            )
    
    def get_logger(self, name: str) -> logging.Logger:
        """Obtiene un logger con nombre específico"""
        return logging.getLogger(name)
    
    def log_conversation(self, **kwargs):
        """Proxy para log de conversación"""
        self.conversation_logger.log_conversation(**kwargs)
    
    def log_performance(self, metric_name: str, value: float, **kwargs):
        """Proxy para log de rendimiento"""
        self.performance_logger.log_metric(metric_name, value, **kwargs)
    
    def log_error(self, error: Exception, **kwargs):
        """Proxy para log de errores"""
        self.error_logger.log_error(error, **kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales del sistema de logging"""
        return {
            'conversation_stats': self.conversation_logger.get_conversation_stats(),
            'recent_metrics': self.performance_logger.get_recent_metrics(last_n=50),
            'error_counts': self.error_logger.error_counts,
            'config': self.config
        }


# Singleton global para fácil acceso
logging_manager = LoggingManager()

# Funciones de conveniencia
def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado"""
    return logging_manager.get_logger(name)

def log_conversation(**kwargs):
    """Registra una conversación"""
    logging_manager.log_conversation(**kwargs)

def log_performance(metric: str, value: float, **kwargs):
    """Registra una métrica de rendimiento"""
    logging_manager.log_performance(metric, value, **kwargs)

def log_error(error: Exception, **kwargs):
    """Registra un error"""
    logging_manager.log_error(error, **kwargs)