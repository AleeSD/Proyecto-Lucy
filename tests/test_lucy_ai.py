"""
Tests para Lucy AI
==================

Suite de pruebas para verificar el funcionamiento correcto
de los componentes principales de Lucy AI.
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Importar módulos a testear
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager
from core.database import ConversationDB
from core.utils import get_language, sanitize_input, create_session_id


class TestConfigManager(unittest.TestCase):
    """Tests para el gestor de configuración"""
    
    def setUp(self):
        """Configurar test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, 'test_config.json')
        
        # Configuración de prueba
        self.test_config = {
            "app": {"name": "Test Lucy", "version": "1.0.0"},
            "model": {"default_language": "es", "confidence_threshold": 0.3},
            "paths": {"data_dir": "test_data", "models_dir": "test_models"}
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
    
    def tearDown(self):
        """Limpiar después de cada test"""
        shutil.rmtree(self.test_dir)
    
    def test_load_config(self):
        """Test cargar configuración desde archivo"""
        config_manager = ConfigManager(self.config_path)
        
        self.assertEqual(config_manager.get('app.name'), "Test Lucy")
        self.assertEqual(config_manager.get('model.default_language'), "es")
        self.assertEqual(config_manager.get('model.confidence_threshold'), 0.3)
    
    def test_get_with_default(self):
        """Test obtener valor con default"""
        config_manager = ConfigManager(self.config_path)
        
        # Valor existente
        self.assertEqual(config_manager.get('app.name'), "Test Lucy")
        
        # Valor no existente con default
        self.assertEqual(config_manager.get('nonexistent.key', 'default'), 'default')
    
    def test_set_value(self):
        """Test establecer valor"""
        config_manager = ConfigManager(self.config_path)
        
        config_manager.set('test.new_key', 'new_value')
        self.assertEqual(config_manager.get('test.new_key'), 'new_value')
    
    def test_save_config(self):
        """Test guardar configuración"""
        config_manager = ConfigManager(self.config_path)
        
        config_manager.set('test.saved_key', 'saved_value')
        
        # Guardar en nuevo archivo
        new_path = os.path.join(self.test_dir, 'saved_config.json')
        config_manager.save(new_path)
        
        # Verificar que se guardó
        self.assertTrue(os.path.exists(new_path))
        
        # Cargar y verificar
        new_config_manager = ConfigManager(new_path)
        self.assertEqual(new_config_manager.get('test.saved_key'), 'saved_value')


class TestConversationDB(unittest.TestCase):
    """Tests para la base de datos de conversaciones"""
    
    def setUp(self):
        """Configurar test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_conversations.db')
        self.db = ConversationDB(self.db_path)
    
    def tearDown(self):
        """Limpiar después de cada test"""
        if hasattr(self, 'db'):
            self.db.close()
        shutil.rmtree(self.test_dir)
    
    def test_database_creation(self):
        """Test creación de base de datos"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Verificar que las tablas existen
        stats = self.db.get_database_stats()
        self.assertIn('total_conversations', stats)
        self.assertIn('total_sessions', stats)
    
    def test_save_conversation(self):
        """Test guardar conversación"""
        conversation_id = self.db.save_conversation(
            session_id='test_session',
            user_input='Hola',
            bot_response='¡Hola! ¿Cómo puedo ayudarte?',
            language='es',
            confidence=0.95,
            intent='saludos',
            response_time=0.5
        )
        
        self.assertIsInstance(conversation_id, int)
        self.assertGreater(conversation_id, 0)
    
    def test_get_conversation_history(self):
        """Test obtener historial de conversación"""
        session_id = 'test_session_history'
        
        # Guardar algunas conversaciones
        conversations = [
            ('Hola', '¡Hola!'),
            ('¿Cómo estás?', 'Muy bien, gracias'),
            ('Adiós', '¡Hasta luego!')
        ]
        
        for user_msg, bot_msg in conversations:
            self.db.save_conversation(
                session_id=session_id,
                user_input=user_msg,
                bot_response=bot_msg,
                language='es'
            )
        
        # Obtener historial
        history = self.db.get_conversation_history(session_id, limit=5)
        
        self.assertEqual(len(history), 3)
        # El historial debe estar en orden inverso (más reciente primero)
        self.assertEqual(history[0]['user_input'], 'Adiós')
        self.assertEqual(history[2]['user_input'], 'Hola')
    
    def test_get_metrics_summary(self):
        """Test obtener resumen de métricas"""
        # Guardar algunas conversaciones
        for i in range(5):
            self.db.save_conversation(
                session_id=f'session_{i}',
                user_input=f'Mensaje {i}',
                bot_response=f'Respuesta {i}',
                language='es',
                confidence=0.8 + (i * 0.02)  # Diferentes confianzas
            )
        
        summary = self.db.get_metrics_summary(hours=24)
        
        self.assertEqual(summary['total_conversations'], 5)
        self.assertGreater(summary['average_confidence'], 0.8)
        self.assertEqual(summary['active_sessions'], 5)


class TestUtils(unittest.TestCase):
    """Tests para utilidades"""
    
    def test_get_language_spanish(self):
        """Test detección de idioma español"""
        spanish_texts = [
            "Hola, ¿cómo estás?",
            "¿Qué tal tu día?",
            "Gracias por tu ayuda",
            "Buenos días"
        ]
        
        for text in spanish_texts:
            with self.subTest(text=text):
                lang = get_language(text)
                self.assertEqual(lang, 'es')
    
    def test_get_language_english(self):
        """Test detección de idioma inglés"""
        english_texts = [
            "Hello, how are you?",
            "Thank you for your help",
            "Good morning",
            "What can you do?"
        ]
        
        for text in english_texts:
            with self.subTest(text=text):
                lang = get_language(text)
                self.assertEqual(lang, 'en')
    
    def test_sanitize_input(self):
        """Test sanitización de entrada"""
        # Texto normal
        self.assertEqual(sanitize_input("Hola mundo"), "Hola mundo")
        
        # Texto con espacios extra
        self.assertEqual(sanitize_input("  Hola mundo  "), "Hola mundo")
        
        # Texto muy largo
        long_text = "a" * 2000
        sanitized = sanitize_input(long_text, max_length=100)
        self.assertEqual(len(sanitized), 100)
        
        # Texto con caracteres de control
        dirty_text = "Hola\x00mundo\x01test"
        clean_text = sanitize_input(dirty_text)
        self.assertEqual(clean_text, "Holamundotest")
    
    def test_create_session_id(self):
        """Test creación de ID de sesión"""
        session_id = create_session_id()
        
        # Verificar formato
        self.assertTrue(session_id.startswith('lucy_'))
        self.assertGreater(len(session_id), 10)
        
        # Verificar unicidad
        session_id2 = create_session_id()
        self.assertNotEqual(session_id, session_id2)


class TestLucyAIIntegration(unittest.TestCase):
    """Tests de integración para Lucy AI"""
    
    def setUp(self):
        """Configurar test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Crear estructura de directorios
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.data_dir = os.path.join(self.test_dir, 'data')
        self.models_dir = os.path.join(self.test_dir, 'data', 'models')
        self.intents_dir = os.path.join(self.test_dir, 'data', 'intents')
        
        os.makedirs(self.config_dir)
        os.makedirs(self.models_dir)
        os.makedirs(self.intents_dir)
        
        # Crear configuración de prueba
        self.config = {
            "app": {"name": "Test Lucy", "version": "1.0.0"},
            "model": {
                "default_language": "es",
                "confidence_threshold": 0.25,
                "supported_languages": ["es", "en"]
            },
            "paths": {
                "data_dir": "data",
                "models_dir": "data/models",
                "intents_dir": "data/intents"
            }
        }
        
        config_path = os.path.join(self.config_dir, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)
        
        # Crear intenciones de prueba
        intents_es = {
            "intents": [
                {
                    "tag": "saludos",
                    "patterns": ["Hola", "Buenos días", "¿Qué tal?"],
                    "responses": ["¡Hola!", "¡Buenos días!", "¡Hola! ¿Cómo puedo ayudarte?"]
                },
                {
                    "tag": "despedida",
                    "patterns": ["Adiós", "Hasta luego", "Nos vemos"],
                    "responses": ["¡Hasta luego!", "¡Adiós!", "¡Nos vemos!"]
                }
            ]
        }
        
        with open(os.path.join(self.intents_dir, 'intents_es.json'), 'w') as f:
            json.dump(intents_es, f)
        
        self.config_path = config_path
    
    def tearDown(self):
        """Limpiar después de cada test"""
        shutil.rmtree(self.test_dir)
    
    @patch('core.lucy_ai.load_model')
    @patch('pickle.load')
    def test_lucy_initialization_without_model(self, mock_pickle, mock_load_model):
        """Test inicialización de Lucy sin modelo entrenado"""
        from core.lucy_ai import LucyAI
        
        # Mock para simular archivos faltantes
        with patch('pathlib.Path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                config_manager = ConfigManager(self.config_path)
                lucy = LucyAI(config_manager)
    
    def test_config_manager_integration(self):
        """Test integración del gestor de configuración"""
        config_manager = ConfigManager(self.config_path)
        
        # Verificar que carga la configuración correctamente
        self.assertEqual(config_manager.get('app.name'), 'Test Lucy')
        self.assertEqual(config_manager.get('model.default_language'), 'es')
        
        # Verificar rutas
        models_path = config_manager.get_path('models_dir')
        self.assertTrue(models_path.endswith('data/models'))


class TestSystemIntegration(unittest.TestCase):
    """Tests de integración del sistema completo"""
    
    def test_import_all_modules(self):
        """Test que todos los módulos se pueden importar correctamente"""
        try:
            from core import ConfigManager, ConversationDB
            from core.utils import get_language, suppress_tf_logs
            from core.training import LucyTrainer
        except ImportError as e:
            self.fail(f"Error importando módulos: {e}")
    
    def test_environment_setup(self):
        """Test que el entorno está configurado correctamente"""
        # Verificar variables de entorno de TensorFlow
        self.assertEqual(os.environ.get('TF_CPP_MIN_LOG_LEVEL'), '3')
        self.assertEqual(os.environ.get('TF_ENABLE_ONEDNN_OPTS'), '0')


def run_basic_tests():
    """Ejecuta solo los tests básicos más importantes"""
    test_suite = unittest.TestSuite()
    
    # Tests básicos más importantes
    test_suite.addTest(TestConfigManager('test_load_config'))
    test_suite.addTest(TestConversationDB('test_database_creation'))
    test_suite.addTest(TestUtils('test_get_language_spanish'))
    test_suite.addTest(TestUtils('test_sanitize_input'))
    test_suite.addTest(TestSystemIntegration('test_import_all_modules'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Tests para Lucy AI')
    parser.add_argument('--basic', action='store_true', 
                    help='Ejecutar solo tests básicos')
    parser.add_argument('--verbose', '-v', action='store_true',
                    help='Output verbose')
    
    args = parser.parse_args()
    
    if args.basic:
        print("🧪 Ejecutando tests básicos...")
        success = run_basic_tests()
        print("✅ Tests básicos completados" if success else "❌ Algunos tests fallaron")
        sys.exit(0 if success else 1)
    else:
        # Ejecutar todos los tests
        unittest.main(verbosity=2 if args.verbose else 1)