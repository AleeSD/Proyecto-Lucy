"""
Gestor de Base de Datos para Lucy AI
===================================

Maneja el almacenamiento persistente de conversaciones, contexto y aprendizaje.
Utiliza SQLite para simplicidad y portabilidad.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

class ConversationDB:
    """Gestor de base de datos para conversaciones y contexto"""
    
    def __init__(self, db_path: str):
        """
        Inicializa la conexión a la base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos
        self._init_database()
    
    def _init_database(self):
        """Inicializa las tablas de la base de datos"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de conversaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    language TEXT NOT NULL,
                    confidence REAL,
                    intent TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    response_time REAL,
                    context TEXT
                )
            ''')
            
            # Tabla de sesiones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_name TEXT,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER DEFAULT 0,
                    preferred_language TEXT DEFAULT 'es',
                    settings TEXT
                )
            ''')
            
            # Tabla de aprendizaje (para futuros patrones)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    response TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    language TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    effectiveness_score REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de métricas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para mejorar rendimiento
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_pattern ON learning_data(pattern)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(last_activity)')
            
            conn.commit()
            self.logger.info("Base de datos inicializada correctamente")
    
    @contextmanager
    def _get_connection(self):
        """Context manager para conexiones a la base de datos"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Error en transacción de base de datos: {e}")
            raise
        finally:
            conn.close()
    
    def save_conversation(self, session_id: str, user_input: str, bot_response: str,
                        language: str, confidence: float = None, intent: str = None,
                        response_time: float = None, context: Dict = None) -> int:
        """
        Guarda una conversación en la base de datos
        
        Args:
            session_id: ID de la sesión
            user_input: Entrada del usuario
            bot_response: Respuesta del bot
            language: Idioma detectado
            confidence: Confianza de la predicción
            intent: Intención detectada
            response_time: Tiempo de respuesta en segundos
            context: Contexto adicional
            
        Returns:
            ID de la conversación guardada
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            context_json = json.dumps(context) if context else None
            
            cursor.execute('''
                INSERT INTO conversations 
                (session_id, user_input, bot_response, language, confidence, 
                intent, response_time, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_input, bot_response, language, 
                confidence, intent, response_time, context_json))
            
            conversation_id = cursor.lastrowid
            
            # Actualizar estadísticas de sesión
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, last_activity, total_messages, preferred_language)
                VALUES (?, CURRENT_TIMESTAMP, 
                        COALESCE((SELECT total_messages FROM sessions WHERE session_id = ?), 0) + 1,
                        ?)
            ''', (session_id, session_id, language))
            
            conn.commit()
            return conversation_id
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene el historial de conversación de una sesión
        
        Args:
            session_id: ID de la sesión
            limit: Número máximo de conversaciones a retornar
            
        Returns:
            Lista de conversaciones
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_input, bot_response, language, confidence, 
                intent, timestamp, response_time
                FROM conversations 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Obtiene información de una sesión
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Información de la sesión o None si no existe
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT session_id, user_name, start_time, last_activity,
                total_messages, preferred_language, settings
                FROM sessions 
                WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_session_settings(self, session_id: str, settings: Dict):
        """
        Actualiza las configuraciones de una sesión
        
        Args:
            session_id: ID de la sesión
            settings: Nuevas configuraciones
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            settings_json = json.dumps(settings)
            
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, last_activity, settings)
                VALUES (?, CURRENT_TIMESTAMP, ?)
            ''', (session_id, settings_json))
            
            conn.commit()
    
    def add_learning_data(self, pattern: str, response: str, intent: str, 
                        language: str, effectiveness_score: float = 0.0):
        """
        Añade datos para el aprendizaje automático
        
        Args:
            pattern: Patrón de entrada
            response: Respuesta asociada
            intent: Intención
            language: Idioma
            effectiveness_score: Puntuación de efectividad
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si ya existe el patrón
            cursor.execute('''
                SELECT id, frequency FROM learning_data 
                WHERE pattern = ? AND intent = ? AND language = ?
            ''', (pattern, intent, language))
            
            existing = cursor.fetchone()
            
            if existing:
                # Incrementar frecuencia y actualizar
                cursor.execute('''
                    UPDATE learning_data 
                    SET frequency = frequency + 1, 
                        last_used = CURRENT_TIMESTAMP,
                        effectiveness_score = ?
                    WHERE id = ?
                ''', (effectiveness_score, existing['id']))
            else:
                # Crear nuevo registro
                cursor.execute('''
                    INSERT INTO learning_data 
                    (pattern, response, intent, language, effectiveness_score)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pattern, response, intent, language, effectiveness_score))
            
            conn.commit()
    
    def get_popular_patterns(self, language: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene los patrones más populares para un idioma
        
        Args:
            language: Idioma a consultar
            limit: Número máximo de patrones
            
        Returns:
            Lista de patrones populares
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT pattern, response, intent, frequency, effectiveness_score
                FROM learning_data 
                WHERE language = ? 
                ORDER BY frequency DESC, effectiveness_score DESC
                LIMIT ?
            ''', (language, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_metric(self, metric_name: str, metric_value: Any):
        """
        Guarda una métrica en la base de datos
        
        Args:
            metric_name: Nombre de la métrica
            metric_value: Valor de la métrica
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO metrics (metric_name, metric_value)
                VALUES (?, ?)
            ''', (metric_name, json.dumps(metric_value)))
            
            conn.commit()
    
    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Obtiene un resumen de métricas
        
        Args:
            hours: Horas hacia atrás para considerar
            
        Returns:
            Resumen de métricas
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            since = datetime.now() - timedelta(hours=hours)
            
            # Total de conversaciones
            cursor.execute('''
                SELECT COUNT(*) as total_conversations
                FROM conversations 
                WHERE timestamp > ?
            ''', (since,))
            total_conversations = cursor.fetchone()['total_conversations']
            
            # Promedio de confianza
            cursor.execute('''
                SELECT AVG(confidence) as avg_confidence
                FROM conversations 
                WHERE timestamp > ? AND confidence IS NOT NULL
            ''', (since,))
            avg_confidence = cursor.fetchone()['avg_confidence']
            
            # Idiomas más usados
            cursor.execute('''
                SELECT language, COUNT(*) as count
                FROM conversations 
                WHERE timestamp > ?
                GROUP BY language
                ORDER BY count DESC
            ''', (since,))
            languages = [dict(row) for row in cursor.fetchall()]
            
            # Sesiones activas
            cursor.execute('''
                SELECT COUNT(DISTINCT session_id) as active_sessions
                FROM conversations 
                WHERE timestamp > ?
            ''', (since,))
            active_sessions = cursor.fetchone()['active_sessions']
            
            return {
                'total_conversations': total_conversations,
                'average_confidence': avg_confidence,
                'languages_usage': languages,
                'active_sessions': active_sessions,
                'period_hours': hours
            }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Limpia datos antiguos de la base de datos
        
        Args:
            days_to_keep: Días de datos a mantener
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Limpiar conversaciones antiguas
            cursor.execute('''
                DELETE FROM conversations 
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            conversations_deleted = cursor.rowcount
            
            # Limpiar métricas antiguas
            cursor.execute('''
                DELETE FROM metrics 
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            metrics_deleted = cursor.rowcount
            
            # Limpiar sesiones inactivas
            cursor.execute('''
                DELETE FROM sessions 
                WHERE last_activity < ?
            ''', (cutoff_date,))
            
            sessions_deleted = cursor.rowcount
            
            conn.commit()
            
            self.logger.info(f"Limpieza completada: {conversations_deleted} conversaciones, "
                        f"{metrics_deleted} métricas, {sessions_deleted} sesiones eliminadas")
            
            return {
                'conversations_deleted': conversations_deleted,
                'metrics_deleted': metrics_deleted,
                'sessions_deleted': sessions_deleted
            }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas generales de la base de datos"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total de registros por tabla
            tables = ['conversations', 'sessions', 'learning_data', 'metrics']
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
                stats[f'total_{table}'] = cursor.fetchone()['count']
            
            # Tamaño de la base de datos
            stats['database_size_bytes'] = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            # Fecha del primer registro
            cursor.execute('''
                SELECT MIN(timestamp) as first_conversation
                FROM conversations
            ''')
            first_conv = cursor.fetchone()['first_conversation']
            stats['first_conversation'] = first_conv
            
            return stats
    
    def backup_database(self, backup_path: str = None) -> str:
        """
        Crea un backup de la base de datos
        
        Args:
            backup_path: Ruta para el backup. Si es None, genera automáticamente.
            
        Returns:
            Ruta del archivo de backup creado
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path.stem}_backup_{timestamp}.db"
        
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Realizar backup usando SQLite
        with self._get_connection() as source_conn:
            with sqlite3.connect(backup_path) as backup_conn:
                source_conn.backup(backup_conn)
        
        self.logger.info(f"Backup creado en: {backup_path}")
        return str(backup_path)
    
    def search_conversations(self, query: str, session_id: str = None, 
                        language: str = None, limit: int = 50) -> List[Dict]:
        """
        Busca conversaciones por texto
        
        Args:
            query: Texto a buscar
            session_id: Filtrar por sesión específica
            language: Filtrar por idioma
            limit: Máximo número de resultados
            
        Returns:
            Lista de conversaciones que coinciden
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            sql = '''
                SELECT * FROM conversations 
                WHERE (user_input LIKE ? OR bot_response LIKE ?)
            '''
            params = [f'%{query}%', f'%{query}%']
            
            if session_id:
                sql += ' AND session_id = ?'
                params.append(session_id)
            
            if language:
                sql += ' AND language = ?'
                params.append(language)
            
            sql += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_context_for_session(self, session_id: str, messages_back: int = 5) -> List[Dict]:
        """
        Obtiene contexto reciente para una sesión
        
        Args:
            session_id: ID de la sesión
            messages_back: Número de mensajes previos a incluir
            
        Returns:
            Lista de mensajes de contexto
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_input, bot_response, intent, timestamp
                FROM conversations 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, messages_back))
            
            results = cursor.fetchall()
            return [dict(row) for row in reversed(results)]
    
    def close(self):
        """Cierra la conexión a la base de datos"""
        # En este caso, usamos context managers, así que no hay conexión persistente
        self.logger.info("Gestor de base de datos cerrado")