#!/usr/bin/env python3
"""
Lucy AI - Asistente de IA Conversacional
========================================

Punto de entrada principal para el asistente Lucy.
Maneja la inicialización, configuración y modo de ejecución.

Uso:
    python lucy.py                    # Modo chat interactivo
    python lucy.py --config custom    # Usar configuración personalizada
    python lucy.py --test            # Ejecutar tests básicos
    python lucy.py --train           # Re-entrenar modelo
    python lucy.py --api             # Modo servidor API

Author: AleeSD
Version: 1.0.0
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Configurar UTF-8 para Windows
if sys.platform == "win32":
    try:
        # Configurar codificación de consola
        os.system("chcp 65001 > nul")
        # Configurar stdout y stderr para UTF-8
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Agregar el directorio actual al path para imports
sys.path.insert(0, str(Path(__file__).parent))

# Configurar entorno antes de importar TensorFlow
from core.utils import suppress_tf_logs

# Suprimir logs de TensorFlow desde el inicio
with suppress_tf_logs():
    from core import LucyAI, ConfigManager, get_config_manager
    from core.database import ConversationDB
    from core.utils import create_session_id, performance_monitor, log_error_with_context


class LucyApplication:
    """Aplicación principal de Lucy AI"""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa la aplicación Lucy
        
        Args:
            config_path: Ruta al archivo de configuración personalizado
        """
        try:
            # Configurar logging básico temporal
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            
            self.logger.info("[ROBOT] Iniciando Lucy AI...")
            
            # Cargar configuración
            self.config_manager = get_config_manager(config_path)
            self.config = self.config_manager.get_all()
            
            # Configurar logging avanzado
            self._setup_logging()
            
            # Inicializar componentes principales
            self.db = None
            self.lucy_ai = None
            self.session_id = create_session_id()
            
            self._initialize_components()
            
        except Exception as e:
            self.logger.error(f"Error inicializando Lucy: {e}")
            raise
    
    def _setup_logging(self):
        """Configura el sistema de logging avanzado"""
        try:
            log_level = self.config.get('logging', {}).get('level', 'INFO')
            
            # Configurar logger raíz
            root_logger = logging.getLogger()
            root_logger.setLevel(getattr(logging, log_level))
            
            # Crear handler de consola si está habilitado
            if self.config.get('logging', {}).get('console_enabled', True):
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.INFO)
                
                formatter = logging.Formatter(
                    self.config.get('logging', {}).get('format', 
                                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
                console_handler.setFormatter(formatter)
                
                root_logger.addHandler(console_handler)
            
            # Crear handler de archivo si está habilitado
            if self.config.get('logging', {}).get('file_enabled', True):
                logs_dir = Path(self.config_manager.get_path('logs_dir'))
                logs_dir.mkdir(exist_ok=True)
                
                file_handler = logging.FileHandler(logs_dir / 'lucy.log', encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                
                detailed_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(detailed_formatter)
                
                root_logger.addHandler(file_handler)
            
            self.logger = logging.getLogger(__name__)
            self.logger.info("[OK] Sistema de logging configurado")
            
        except Exception as e:
            print(f"[WARN] Error configurando logging: {e}")
    
    def _initialize_components(self):
        """Inicializa los componentes principales de Lucy"""
        try:
            performance_monitor.start_timer('initialization')
            
            # Inicializar base de datos
            db_path = self.config.get('database', {}).get('path') or 'data/conversations.db'
            self.db = ConversationDB(db_path)
            self.logger.info("[OK] Base de datos inicializada")
            
            # Inicializar Lucy AI
            with suppress_tf_logs():
                self.lucy_ai = LucyAI(self.config_manager)
            self.logger.info("[OK] Motor de IA inicializado")
            
            init_time = performance_monitor.end_timer('initialization')
            self.logger.info(f"[ROCKET] Lucy inicializada en {init_time:.2f}s")
            
        except Exception as e:
            log_error_with_context(e, {
                'component': 'initialization',
                'session_id': self.session_id
            })
            raise
    
    def run_interactive_chat(self):
        """Ejecuta el modo de chat interactivo"""
        try:
            self.logger.info(f"[CHAT] Iniciando sesión interactiva: {self.session_id}")
            
            # Mensajes de bienvenida
            print("\n" + "="*60)
            print("[ROBOT] Lucy AI - Asistente Inteligente")
            print("="*60)
            print("Hola! Soy Lucy, tu asistente de IA.")
            print("Puedo ayudarte en español e inglés.")
            print("\nComandos especiales:")
            print("• /help    - Mostrar ayuda")
            print("• /config  - Ver configuración")
            print("• /stats   - Ver estadísticas")
            print("• /clear   - Limpiar contexto")
            print("• /exit    - Salir")
            print("-" * 60)
            
            conversation_count = 0
            
            while True:
                try:
                    # Obtener entrada del usuario
                    user_input = input("\n[USER] Tú: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Procesar comandos especiales
                    if user_input.startswith('/'):
                        if self._handle_command(user_input):
                            break
                        continue
                    
                    # Procesar mensaje con Lucy
                    performance_monitor.start_timer('response')
                    response = self.lucy_ai.process_message(user_input)
                    response_time = performance_monitor.end_timer('response')
                    
                    print(f"\n[ROBOT] Lucy: {response}")
                    
                    # Mostrar tiempo de respuesta si está configurado
                    if self.config.get('ui', {}).get('show_response_time', False):
                        print(f"   [CLOCK] Tiempo de respuesta: {response_time:.2f}s")
                    
                    # Guardar conversación en base de datos
                    if self.db:
                        self.db.save_conversation(
                            session_id=self.session_id,
                            user_input=user_input,
                            bot_response=response,
                            language=self.lucy_ai.get_current_language(),
                            confidence=self.lucy_ai.get_last_confidence(),
                            intent=self.lucy_ai.get_last_intent(),
                            response_time=response_time
                        )
                    
                    conversation_count += 1
                    
                except KeyboardInterrupt:
                    print("\n\n[WAVE] ¡Hasta luego!")
                    break
                except Exception as e:
                    log_error_with_context(e, {
                        'user_input': user_input,
                        'session_id': self.session_id,
                        'conversation_count': conversation_count
                    })
                    print("[X] Lo siento, ocurrió un error. Intenta de nuevo.")
            
            # Estadísticas de sesión
            self.logger.info(f"[CHART] Sesión finalizada: {conversation_count} conversaciones")
            
        except Exception as e:
            log_error_with_context(e, {'mode': 'interactive_chat'})
            print("[X] Error crítico en modo interactivo")
    
    def _handle_command(self, command: str) -> bool:
        """
        Maneja comandos especiales del usuario
        
        Args:
            command: Comando ingresado por el usuario
            
        Returns:
            True si debe salir del programa
        """
        command = command.lower().strip()
        
        if command in ['/exit', '/quit', '/salir']:
            print("[WAVE] ¡Hasta pronto!")
            return True
        
        elif command == '/help':
            self._show_help()
        
        elif command == '/config':
            self._show_config()
        
        elif command == '/stats':
            self._show_stats()
        
        elif command == '/clear':
            if hasattr(self.lucy_ai, 'clear_context'):
                self.lucy_ai.clear_context()
            print("[BROOM] Contexto limpiado")
        
        elif command == '/debug':
            self._show_debug_info()
        
        else:
            print(f"[?] Comando desconocido: {command}")
            print("   Escribe /help para ver comandos disponibles")
        
        return False
    
    def _show_help(self):
        """Muestra ayuda de comandos"""
        print("\n[BOOK] Comandos Disponibles:")
        print("• /help    - Mostrar esta ayuda")
        print("• /config  - Ver configuración actual")
        print("• /stats   - Ver estadísticas de sesión")
        print("• /clear   - Limpiar contexto de conversación")
        print("• /debug   - Información de debug")
        print("• /exit    - Salir del programa")
    
    def _show_config(self):
        """Muestra configuración actual"""
        print("\n[GEAR] Configuración Actual:")
        print(f"• Idioma por defecto: {self.config.get('model', {}).get('default_language', 'es')}")
        print(f"• Umbral de confianza: {self.config.get('model', {}).get('confidence_threshold', 0.25)}")
        print(f"• Base de datos: {'[OK] Habilitada' if self.db else '[X] Deshabilitada'}")
        print(f"• Logging: {self.config.get('logging', {}).get('level', 'INFO')}")
    
    def _show_stats(self):
        """Muestra estadísticas de la sesión"""
        if self.db:
            try:
                stats = self.db.get_metrics_summary(hours=1)
                print("\n[CHART] Estadísticas:")
                print(f"• Conversaciones esta hora: {stats.get('total_conversations', 0)}")
                print(f"• Confianza promedio: {stats.get('average_confidence', 0):.2%}")
                print(f"• Sesiones activas: {stats.get('active_sessions', 0)}")
                
                # Métricas de rendimiento
                metrics = performance_monitor.get_metrics()
                if metrics:
                    print("• Rendimiento:")
                    for operation, data in metrics.items():
                        if 'duration' in data:
                            print(f"  - {operation}: {data['duration']:.2f}s")
            except Exception as e:
                print(f"[X] Error obteniendo estadísticas: {e}")
        else:
            print("[CHART] Base de datos no disponible para estadísticas")
    
    def _show_debug_info(self):
        """Muestra información de debug"""
        print("\n[WRENCH] Información de Debug:")
        print(f"• Session ID: {self.session_id}")
        print(f"• Lucy AI: {'[OK] OK' if self.lucy_ai else '[X] Error'}")
        print(f"• Base de datos: {'[OK] OK' if self.db else '[X] Error'}")
        print(f"• Config path: {self.config_manager.config_path}")
        
        if hasattr(self.lucy_ai, 'get_model_info'):
            model_info = self.lucy_ai.get_model_info()
            print(f"• Modelo cargado: {'[OK] OK' if model_info else '[X] Error'}")
    
    def run_tests(self):
        """Ejecuta tests básicos del sistema"""
        print("[TEST] Ejecutando tests básicos...")
        
        tests_passed = 0
        tests_total = 0
        
        # Test 1: Configuración
        tests_total += 1
        try:
            config_test = self.config_manager.get('app.name')
            if config_test:
                print("[OK] Test configuración: OK")
                tests_passed += 1
            else:
                print("[X] Test configuración: FAIL")
        except Exception as e:
            print(f"[X] Test configuración: ERROR - {e}")
        
        # Test 2: Base de datos
        tests_total += 1
        try:
            if self.db:
                stats = self.db.get_database_stats()
                print("[OK] Test base de datos: OK")
                tests_passed += 1
            else:
                print("[X] Test base de datos: FAIL")
        except Exception as e:
            print(f"[X] Test base de datos: ERROR - {e}")
        
        # Test 3: Lucy AI
        tests_total += 1
        try:
            if self.lucy_ai:
                response = self.lucy_ai.process_message("test")
                if response:
                    print("[OK] Test Lucy AI: OK")
                    tests_passed += 1
                else:
                    print("[X] Test Lucy AI: FAIL - No response")
            else:
                print("[X] Test Lucy AI: FAIL - Not initialized")
        except Exception as e:
            print(f"[X] Test Lucy AI: ERROR - {e}")
        
        # Resumen
        print(f"\n[CHART] Resultado: {tests_passed}/{tests_total} tests pasaron")
        if tests_passed == tests_total:
            print("[PARTY] ¡Todos los tests pasaron!")
            return True
        else:
            print("[WARN] Algunos tests fallaron")
            return False
    
    def run_training(self):
        """Ejecuta re-entrenamiento del modelo"""
        print("[BRAIN] Iniciando re-entrenamiento del modelo...")
        
        try:
            if hasattr(self.lucy_ai, 'retrain_model'):
                self.lucy_ai.retrain_model()
                print("[OK] Re-entrenamiento completado")
            else:
                print("[X] Función de re-entrenamiento no disponible")
                
        except Exception as e:
            print(f"[X] Error en re-entrenamiento: {e}")


def main():
    """Función principal de la aplicación"""
    parser = argparse.ArgumentParser(
        description="Lucy AI - Asistente de IA Conversacional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
python lucy.py                    # Modo chat interactivo
python lucy.py --config custom    # Configuración personalizada  
python lucy.py --test            # Ejecutar tests
python lucy.py --train           # Re-entrenar modelo
        """
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        help='Ruta al archivo de configuración personalizado'
    )
    
    parser.add_argument(
        '--test', 
        action='store_true', 
        help='Ejecutar tests básicos del sistema'
    )
    
    parser.add_argument(
        '--train', 
        action='store_true', 
        help='Re-entrenar el modelo'
    )
    
    parser.add_argument(
        '--api', 
        action='store_true', 
        help='Iniciar en modo servidor API'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Activar modo debug'
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version='Lucy AI v1.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Inicializar aplicación
        app = LucyApplication(config_path=args.config)
        
        # Ejecutar según el modo solicitado
        if args.test:
            success = app.run_tests()
            sys.exit(0 if success else 1)
        
        elif args.train:
            app.run_training()
        
        elif args.api:
            print("[GLOBE] Modo API no implementado aún")
            print("   Será implementado en fases futuras del desarrollo")
        
        else:
            # Modo chat interactivo por defecto
            app.run_interactive_chat()
    
    except KeyboardInterrupt:
        print("\n[WAVE] Programa interrumpido por el usuario")
        sys.exit(0)
    
    except Exception as e:
        print(f"[X] Error crítico: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()