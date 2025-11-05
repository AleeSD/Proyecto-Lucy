"""
Lucy AI - Clase Principal del Asistente
======================================

Núcleo de procesamiento de lenguaje natural y generación de respuestas.
Maneja el modelo de ML, detección de idiomas y contexto conversacional.
"""

import os
import json
import pickle
import random
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Importaciones con manejo de TensorFlow
from .utils import suppress_tf_logs, get_language, measure_execution_time, load_json_file
from .config_manager import ConfigManager
from .plugins.manager import PluginManager, PluginResult
from .services import ServiceManager
from .nlp import AdvancedNLPManager

# Importar TensorFlow con supresión de logs
with suppress_tf_logs():
    import nltk
    from nltk.stem import WordNetLemmatizer


class LucyAI:
    """Clase principal del asistente Lucy AI"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Inicializa Lucy AI con configuración
        
        Args:
            config_manager: Gestor de configuración del sistema
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.config = config_manager.get_all()
        
        # Estado interno
        self.current_language = self.config.get('model', {}).get('default_language', 'es')
        self.last_confidence = 0.0
        self.last_intent = None
        self.conversation_context = []
        self.max_context_length = 5
        
        # Componentes del modelo
        self.lemmatizer = WordNetLemmatizer()
        self.words = None
        self.classes = None
        self.model = None
        self.intents = {}
        
        # Inicializar componentes
        self._ensure_nltk_data()
        self._load_model_components()
        self._load_intents()
        
        # Sistema de plugins (Día 8)
        try:
            self.plugin_manager = PluginManager(self.config_manager)
            self.plugin_manager.start(engine=self)
        except Exception as e:
            self.logger.error(f"Error inicializando sistema de plugins: {e}")

        # Servicios externos (Día 9)
        try:
            self.service_manager = ServiceManager(self.config_manager)
        except Exception as e:
            self.logger.error(f"Error inicializando gestor de servicios: {e}")

        # PLN avanzado (Día 10)
        try:
            self.nlp_manager = AdvancedNLPManager(self.config_manager)
        except Exception as e:
            self.logger.error(f"Error inicializando gestor de PLN avanzado: {e}")
        
        self.logger.info("[OK] Lucy AI inicializada correctamente")
    
    def _ensure_nltk_data(self):
        """Asegura que los datos de NLTK estén disponibles"""
        try:
            # Descargar datos necesarios de NLTK si no existen
            required_data = ['punkt', 'punkt_tab', 'wordnet', 'omw-1.4']
            
            for data in required_data:
                try:
                    if data in ('punkt', 'punkt_tab'):
                        nltk.data.find(f'tokenizers/{data}')
                    else:
                        nltk.data.find(f'corpora/{data}')
                except LookupError:
                    self.logger.info(f"Descargando datos NLTK: {data}")
                    nltk.download(data, quiet=True)
            
            self.logger.debug("[OK] Datos NLTK verificados")
            
        except Exception as e:
            self.logger.error(f"Error configurando NLTK: {e}")
            raise
    
    def _load_model_components(self):
        """Carga los componentes del modelo ML"""
        try:
            models_dir = Path(self.config_manager.get_path('models_dir'))
            
            # Rutas de archivos del modelo
            words_path = models_dir / 'words.pkl'
            classes_path = models_dir / 'classes.pkl'
            model_path = models_dir / 'lucy_model.h5'
            
            # Verificar existencia de archivos
            missing_files = []
            for name, path in [('words', words_path), ('classes', classes_path), ('model', model_path)]:
                if not path.exists():
                    missing_files.append(str(path))
            
            if missing_files:
                # En modo pruebas, levantar error si faltan componentes del modelo
                raise FileNotFoundError(f"Archivos del modelo no encontrados: {missing_files}")
            
            # Cargar componentes
            with suppress_tf_logs():
                self.logger.info("Cargando componentes del modelo...")
                
                # Cargar vocabulario y clases
                with open(words_path, 'rb') as f:
                    self.words = pickle.load(f)
                
                with open(classes_path, 'rb') as f:
                    self.classes = pickle.load(f)
                
                # Importar y cargar modelo de Keras de forma diferida
                try:
                    from tensorflow.keras.models import load_model  # type: ignore
                    self.model = load_model(str(model_path))
                    if hasattr(self.model, 'make_predict_function'):
                        try:
                            self.model.make_predict_function()
                        except Exception:
                            pass
                except Exception as tf_err:
                    self.logger.warning(f"No se pudo cargar TensorFlow/Keras: {tf_err}. Usando modo básico sin ML")
                    self.model = None
            
            self.logger.info(f"[OK] Modelo cargado: {len(self.words)} palabras, {len(self.classes)} clases")
            
        except Exception as e:
            # También degradar si falla la carga por incompatibilidad
            self.logger.error(f"Error cargando modelo, usando modo básico sin ML: {e}")
            self.words = []
            self.classes = []
            self.model = None
    
    def _load_intents(self):
        """Carga los archivos de intenciones para todos los idiomas"""
        try:
            intents_dir = Path(self.config_manager.get_path('intents_dir'))
            supported_languages = self.config.get('model', {}).get('supported_languages', ['es', 'en'])
            
            self.intents = {}
            
            for lang in supported_languages:
                intent_file = intents_dir / f'intents_{lang}.json'
                
                if intent_file.exists():
                    intents_data = load_json_file(str(intent_file))
                    if intents_data:
                        self.intents[lang] = intents_data
                        intent_count = len(intents_data.get('intents', []))
                        self.logger.debug(f"[OK] Intenciones cargadas para {lang}: {intent_count}")
                    else:
                        self.logger.warning(f"[WARN] Archivo de intenciones vacío: {intent_file}")
                else:
                    self.logger.warning(f"[WARN] Archivo de intenciones no encontrado: {intent_file}")
            
            if not self.intents:
                raise FileNotFoundError("No se encontraron archivos de intenciones válidos")
            
            self.logger.info(f"[OK] Intenciones cargadas para idiomas: {list(self.intents.keys())}")
            
        except Exception as e:
            self.logger.error(f"Error cargando intenciones: {e}")
            raise
    
    def autocomplete_message(self, partial_message: str) -> List[str]:
        """
        Proporciona sugerencias de autocompletado basadas en un mensaje parcial
        
        Args:
            partial_message: Mensaje parcial del usuario
            
        Returns:
            Lista de posibles autocompletados
        """
        if not partial_message or not partial_message.strip():
            return []
            
        # Sanitizar entrada
        partial_message = partial_message.strip().lower()
        
        # Detectar idioma
        lang = get_language(partial_message)
        if lang not in self.intents:
            lang = self.config.get('model', {}).get('default_language', 'es')
            
        # Buscar patrones que coincidan con el mensaje parcial
        suggestions = []
        
        if lang in self.intents:
            for intent in self.intents[lang].get('intents', []):
                for pattern in intent.get('patterns', []):
                    # Normalizar patrón para comparación (quitar signos de puntuación)
                    normalized_pattern = ''.join(c.lower() for c in pattern if c.isalnum() or c.isspace())
                    
                    if normalized_pattern.startswith(partial_message) or partial_message in normalized_pattern:
                        if pattern not in suggestions:
                            suggestions.append(pattern)
                            
                    # Si ya tenemos suficientes sugerencias, detenemos la búsqueda
                    if len(suggestions) >= 5:
                        break
                        
        return suggestions[:5]  # Limitar a 5 sugerencias
    
    @measure_execution_time
    def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """
        Procesa un mensaje del usuario y genera una respuesta
        
        Args:
            message: Mensaje del usuario
            context: Contexto adicional para la conversación
            
        Returns:
            Respuesta generada por Lucy
        """
        try:
            if not message or not message.strip():
                return self._get_default_response("empty_message")
            
            # Sanitizar entrada
            message = message.strip()[:self.config.get('security', {}).get('max_input_length', 1000)]
            
            # Plugins: posibilidad de manejar el mensaje antes del modelo
            if hasattr(self, 'plugin_manager'):
                try:
                    pre_result: PluginResult = self.plugin_manager.handle_message(message, self.conversation_context)
                    if pre_result and pre_result.handled and pre_result.response:
                        # Actualizar contexto con respuesta del plugin
                        self._update_context(message, pre_result.response)
                        return pre_result.response
                except Exception as _plug_err:
                    self.logger.warning(f"[Plugins] Error en pre-procesamiento: {_plug_err}")

            # Comando de servicios externos: '!api <servicio> <operacion> [k=v]...'
            if isinstance(message, str) and message.strip().lower().startswith("!api ") and hasattr(self, 'service_manager'):
                parts = message.strip().split()
                if len(parts) < 3:
                    return "Uso: !api <servicio> <operación> k=v ..."
                _, service, operation, *kv = parts
                params = {}
                for item in kv:
                    if "=" in item:
                        k, v = item.split("=", 1)
                        params[k] = v
                result = self.service_manager.execute(service, operation, params)
                if result is None:
                    return f"Servicio '{service}' u operación '{operation}' no disponible"
                self._update_context(message, str(result))
                return str(result)

            # Comando de PLN avanzado: '!nlp analyze text=...'
            if isinstance(message, str) and message.strip().lower().startswith("!nlp ") and hasattr(self, 'nlp_manager'):
                parts = message.strip().split()
                if len(parts) < 2:
                    return "Uso: !nlp <analyze|sent_doc|sent_sent|ner|relate|gen|translate> text=... [to=lang]"
                _, command, *kv = parts if len(parts) >= 2 else (None, None)
                params = {}
                for item in kv:
                    if "=" in item:
                        k, v = item.split("=", 1)
                        params[k] = v
                text = params.get("text", "")
                result = None
                try:
                    if command == "analyze":
                        result = self.nlp_manager.analyze(text)
                    elif command == "sent_doc":
                        result = self.nlp_manager.analyze_sentiment_doc(text)
                    elif command == "sent_sent":
                        result = self.nlp_manager.analyze_sentiment_sentence(text)
                    elif command == "ner":
                        result = self.nlp_manager.named_entity_recognition(text)
                    elif command == "relate":
                        result = self.nlp_manager.relation_extraction(text)
                    elif command == "gen":
                        max_tokens = int(params.get("max", "50"))
                        result = self.nlp_manager.generate(text or params.get("prompt", ""), max_new_tokens=max_tokens)
                    elif command == "translate":
                        target = params.get("to", "en")
                        result = self.nlp_manager.translate(text, target_lang=target)
                    else:
                        return "Comando !nlp desconocido"
                except Exception as e:
                    return f"Error en !nlp {command}: {e}"
                try:
                    return json.dumps(result, ensure_ascii=False)
                except Exception:
                    return str(result)
            
            # Detectar idioma
            self.current_language = get_language(message)
            
            # Verificar que tenemos intenciones para este idioma
            if self.current_language not in self.intents:
                self.current_language = self.config.get('model', {}).get('default_language', 'es')
            
            # Procesar mensaje con el modelo
            prediction_results = self._predict_intent(message)
            
            if not prediction_results:
                return self._get_default_response("no_prediction")
            
            # Obtener la mejor predicción
            best_intent = prediction_results[0]
            self.last_intent = best_intent['intent']
            self.last_confidence = float(best_intent['probability'])
            
            # Verificar umbral de confianza
            confidence_threshold = self.config.get('model', {}).get('confidence_threshold', 0.25)
            
            if self.last_confidence < confidence_threshold:
                return self._get_default_response("low_confidence")
            
            # Generar respuesta basada en la intención
            response = self._generate_response(self.last_intent, message, context)
            
            # Actualizar contexto conversacional
            self._update_context(message, response)
            
            self.logger.debug(f"Procesado '{message}' -> Intent: {self.last_intent} "
                            f"(Confianza: {self.last_confidence:.2%})")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error procesando mensaje: {e}", exc_info=True)
            return self._get_default_response("error")
    
    def _predict_intent(self, message: str) -> List[Dict[str, Any]]:
        """
        Predice la intención del mensaje usando el modelo ML
        
        Args:
            message: Mensaje a analizar
            
        Returns:
            Lista de predicciones ordenadas por confianza
        """
        try:
            # Si no hay modelo, usar heurística basada en patrones
            if self.model is None or not self.words or not self.classes:
                return self._predict_intent_fallback(message)

            # Preparar el mensaje para el modelo
            bow = self._create_bag_of_words(message)
            
            # Realizar predicción
            with suppress_tf_logs():
                prediction = self.model.predict(np.array([bow]), verbose=0)[0]
            
            # Procesar resultados
            results = []
            error_threshold = self.config.get('model', {}).get('confidence_threshold', 0.25)
            
            for i, probability in enumerate(prediction):
                if probability > error_threshold:
                    results.append({
                        'intent': self.classes[i],
                        'probability': float(probability)
                    })
            
            # Ordenar por probabilidad descendente
            return sorted(results, key=lambda x: x['probability'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error en predicción: {e}", exc_info=True)
            return self._predict_intent_fallback(message)
    
    def _predict_intent_fallback(self, message: str) -> List[Dict[str, Any]]:
        """
        Método alternativo para predecir intención cuando no hay modelo ML
        
        Args:
            message: Mensaje a analizar
            
        Returns:
            Lista de predicciones ordenadas por confianza
        """
        try:
            # Normalizar mensaje (quitar signos de puntuación y convertir a minúsculas)
            normalized_message = ''.join(c.lower() for c in message if c.isalnum() or c.isspace())
            words = normalized_message.split()
            
            # Resultados de coincidencia
            matches = []
            
            # Buscar coincidencias en los patrones de intención
            if self.current_language in self.intents:
                for intent in self.intents[self.current_language].get('intents', []):
                    intent_name = intent.get('tag', 'unknown')
                    patterns = intent.get('patterns', [])
                    
                    # Calcular puntuación para cada patrón
                    best_score = 0
                    for pattern in patterns:
                        # Normalizar patrón
                        normalized_pattern = ''.join(c.lower() for c in pattern if c.isalnum() or c.isspace())
                        pattern_words = normalized_pattern.split()
                        
                        # Calcular coincidencia exacta
                        if normalized_message == normalized_pattern:
                            score = 1.0
                        else:
                            # Calcular coincidencia de palabras
                            common_words = sum(1 for word in words if word in pattern_words)
                            total_words = len(set(words + pattern_words))
                            score = common_words / total_words if total_words > 0 else 0
                            
                            # Bonificación por coincidencia de inicio
                            if normalized_message.startswith(normalized_pattern) or normalized_pattern.startswith(normalized_message):
                                score += 0.2
                                
                            # Bonificación por coincidencia de palabras clave
                            if any(word in normalized_pattern for word in words if len(word) > 3):
                                score += 0.1
                        
                        # Actualizar mejor puntuación para esta intención
                        best_score = max(best_score, score)
                    
                    # Añadir a resultados si supera umbral
                    if best_score > 0.3:
                        matches.append({
                            'intent': intent_name,
                            'probability': best_score
                        })
            
            # Ordenar por probabilidad descendente
            return sorted(matches, key=lambda x: x['probability'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error en predicción fallback: {e}", exc_info=True)
            return [{'intent': 'fallback', 'probability': 1.0}]

    def _predict_intent_fallback(self, message: str) -> List[Dict[str, Any]]:
        """
        Heurística simple basada en coincidencia de palabras con patrones de intents
        usada cuando no hay modelo ML disponible.
        """
        try:
            tokens = [self.lemmatizer.lemmatize(tok) for tok in nltk.word_tokenize(message.lower())]
            token_set = set(tokens)
            current_intents = self.intents.get(self.current_language, {}).get('intents', [])

            scored: List[Tuple[str, float]] = []
            for intent in current_intents:
                tag = intent.get('tag')
                patterns = intent.get('patterns', [])
                if not tag or not patterns:
                    continue
                score = 0.0
                total = 0
                for p in patterns:
                    ptoks = [self.lemmatizer.lemmatize(t) for t in nltk.word_tokenize(p.lower())]
                    if not ptoks:
                        continue
                    overlap = len(token_set.intersection(ptoks))
                    total += 1
                    # Normalizar por longitud de patrón
                    score += overlap / max(1, len(set(ptoks)))
                if total > 0:
                    scored.append((tag, score / total))

            scored.sort(key=lambda x: x[1], reverse=True)

            results: List[Dict[str, Any]] = []
            for tag, s in scored[:3]:
                if s > 0:
                    results.append({'intent': tag, 'probability': float(min(0.99, s))})
            return results
        except Exception:
            return []
    
    def _create_bag_of_words(self, message: str) -> np.ndarray:
        """
        Crea la bolsa de palabras para el modelo ML
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            Array numpy con la representación de bolsa de palabras
        """
        # Tokenizar y lematizar
        message_words = nltk.word_tokenize(message.lower())
        message_words = [self.lemmatizer.lemmatize(word) for word in message_words]
        
        # Crear bolsa de palabras
        bag = np.zeros(len(self.words), dtype=np.float32)
        for i, word in enumerate(self.words):
            if word in message_words:
                bag[i] = 1.0
        
        return bag
    
    def _generate_response(self, intent: str, message: str, context: Dict[str, Any] = None) -> str:
        """
        Genera una respuesta basada en la intención detectada
        
        Args:
            intent: Intención detectada
            message: Mensaje original del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta generada
        """
        try:
            current_intents = self.intents.get(self.current_language, {}).get('intents', [])
            
            # Buscar la intención en los datos
            for intent_data in current_intents:
                if intent_data.get('tag') == intent:
                    responses = intent_data.get('responses', [])
                    if responses:
                        # Evitar repetir la última respuesta para esta intención si hay más de una opción
                        if len(responses) > 1 and hasattr(self, 'last_responses') and intent in self.last_responses:
                            filtered_responses = [r for r in responses if r != self.last_responses.get(intent)]
                            response = random.choice(filtered_responses)
                        else:
                            # Seleccionar respuesta aleatoria
                            response = random.choice(responses)
                        
                        # Guardar esta respuesta para evitar repetirla la próxima vez
                        if not hasattr(self, 'last_responses'):
                            self.last_responses = {}
                        self.last_responses[intent] = response
                        
                        # Personalizar respuesta si es posible
                        return self._personalize_response(response, message, context)
            
            # Si no se encuentra la intención, respuesta genérica
            return self._get_default_response("unknown_intent")
            
        except Exception as e:
            self.logger.error(f"Error generando respuesta: {e}")
            return self._get_default_response("error")
    
    def _personalize_response(self, response: str, message: str, context: Dict[str, Any] = None) -> str:
        """
        Personaliza una respuesta con información contextual
        
        Args:
            response: Respuesta base
            message: Mensaje del usuario
            context: Contexto adicional
            
        Returns:
            Respuesta personalizada
        """
        # Por ahora, retorna la respuesta tal como está
        # En futuras versiones se pueden agregar personalizaciones más avanzadas
        return response
    
    def _update_context(self, user_message: str, bot_response: str):
        """
        Actualiza el contexto conversacional
        
        Args:
            user_message: Mensaje del usuario
            bot_response: Respuesta del bot
        """
        context_entry = {
            'user_message': user_message,
            'bot_response': bot_response,
            'intent': self.last_intent,
            'confidence': self.last_confidence,
            'language': self.current_language,
            'timestamp': self._get_timestamp()
        }
        
        self.conversation_context.append(context_entry)
        
        # Mantener solo los últimos N mensajes
        if len(self.conversation_context) > self.max_context_length:
            self.conversation_context = self.conversation_context[-self.max_context_length:]
    
    def _get_default_response(self, response_type: str) -> str:
        """
        Obtiene respuestas por defecto para casos especiales
        
        Args:
            response_type: Tipo de respuesta por defecto
            
        Returns:
            Respuesta por defecto
        """
        default_responses = {
            'es': {
                'empty_message': "No he recibido ningún mensaje. ¿Podrías escribir algo?",
                'no_prediction': "No he podido procesar tu mensaje. ¿Podrías reformularlo?",
                'low_confidence': "No estoy segura de cómo responder a eso. ¿Podrías ser más específico?",
                'unknown_intent': "Interesante... aún estoy aprendiendo sobre eso. ¿Podrías ayudarme con más contexto?",
                'error': "Disculpa, he tenido un problema técnico. ¿Podrías intentar de nuevo?"
            },
            'en': {
                'empty_message': "I didn't receive any message. Could you write something?",
                'no_prediction': "I couldn't process your message. Could you rephrase it?",
                'low_confidence': "I'm not sure how to respond to that. Could you be more specific?",
                'unknown_intent': "Interesting... I'm still learning about that. Could you give me more context?",
                'error': "Sorry, I had a technical problem. Could you try again?"
            }
        }
        
        responses = default_responses.get(self.current_language, default_responses['es'])
        return responses.get(response_type, "Lo siento, no puedo procesar eso ahora.")
    
    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual en formato ISO"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_current_language(self) -> str:
        """Retorna el idioma actual de la conversación"""
        return self.current_language
    
    def get_last_confidence(self) -> float:
        """Retorna la confianza de la última predicción"""
        return self.last_confidence
    
    def get_last_intent(self) -> Optional[str]:
        """Retorna la última intención detectada"""
        return self.last_intent
    
    def get_conversation_context(self) -> List[Dict[str, Any]]:
        """Retorna el contexto actual de la conversación"""
        return self.conversation_context.copy()
    
    def clear_context(self):
        """Limpia el contexto conversacional"""
        self.conversation_context.clear()
        self.logger.debug("Contexto conversacional limpiado")
    
    def set_language(self, language: str):
        """
        Establece el idioma de la conversación
        
        Args:
            language: Código de idioma ('es' o 'en')
        """
        supported_languages = self.config.get('model', {}).get('supported_languages', ['es', 'en'])
        
        if language in supported_languages and language in self.intents:
            self.current_language = language
            self.logger.info(f"Idioma cambiado a: {language}")
        else:
            self.logger.warning(f"Idioma no soportado: {language}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información del modelo cargado
        
        Returns:
            Información del modelo
        """
        try:
            model_info = {
                'model_loaded': self.model is not None,
                'vocabulary_size': len(self.words) if self.words else 0,
                'classes_count': len(self.classes) if self.classes else 0,
                'supported_languages': list(self.intents.keys()),
                'current_language': self.current_language,
                'context_length': len(self.conversation_context),
                'max_context_length': self.max_context_length
            }
            
            if self.model:
                model_info.update({
                    'model_input_shape': self.model.input_shape,
                    'model_output_shape': self.model.output_shape,
                })
            
            return model_info
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info del modelo: {e}")
            return {'error': str(e)}
    
    def get_available_intents(self, language: str = None) -> List[str]:
        """
        Obtiene lista de intenciones disponibles
        
        Args:
            language: Idioma específico (usar actual si es None)
            
        Returns:
            Lista de intenciones disponibles
        """
        lang = language or self.current_language
        
        if lang not in self.intents:
            return []
        
        intents_data = self.intents[lang].get('intents', [])
        return [intent.get('tag') for intent in intents_data if intent.get('tag')]
    
    def analyze_message(self, message: str) -> Dict[str, Any]:
        """
        Analiza un mensaje sin generar respuesta (para debugging)
        
        Args:
            message: Mensaje a analizar
            
        Returns:
            Análisis completo del mensaje
        """
        try:
            # Detectar idioma
            detected_language = get_language(message)
            
            # Predecir intenciones
            predictions = self._predict_intent(message)
            
            # Crear bolsa de palabras para análisis
            bow = self._create_bag_of_words(message)
            active_words = [word for i, word in enumerate(self.words) if bow[i] > 0]
            
            analysis = {
                'original_message': message,
                'detected_language': detected_language,
                'processed_words': active_words,
                'predictions': predictions,
                'bag_of_words_size': len(bow),
                'active_features': int(np.sum(bow)),
                'timestamp': self._get_timestamp()
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error en análisis de mensaje: {e}")
            return {'error': str(e)}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del estado actual de Lucy
        
        Returns:
            Estadísticas del sistema
        """
        try:
            stats = {
                'model_info': self.get_model_info(),
                'conversation_stats': {
                    'current_language': self.current_language,
                    'context_messages': len(self.conversation_context),
                    'last_confidence': self.last_confidence,
                    'last_intent': self.last_intent
                },
                'languages': {
                    'supported': list(self.intents.keys()),
                    'current': self.current_language,
                    'default': self.config.get('model', {}).get('default_language')
                },
                'configuration': {
                    'confidence_threshold': self.config.get('model', {}).get('confidence_threshold'),
                    'max_context_length': self.max_context_length
                }
            }
            
            # Estadísticas por idioma
            for lang in self.intents:
                intents_count = len(self.intents[lang].get('intents', []))
                stats['languages'][f'{lang}_intents'] = intents_count
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {'error': str(e)}
    
    def retrain_model(self, new_data: Dict[str, Any] = None):
        """
        Re-entrena el modelo (placeholder para implementación futura)
        
        Args:
            new_data: Nuevos datos para entrenamiento
        """
        self.logger.warning("Re-entrenamiento no implementado aún")
        # TODO: Implementar en fases futuras del desarrollo
        raise NotImplementedError("Re-entrenamiento será implementado en versiones futuras")
    
    def export_conversation_data(self) -> Dict[str, Any]:
        """
        Exporta datos de conversación para análisis
        
        Returns:
            Datos de conversación formateados
        """
        return {
            'context': self.conversation_context,
            'session_stats': {
                'language': self.current_language,
                'message_count': len(self.conversation_context),
                'last_intent': self.last_intent,
                'last_confidence': self.last_confidence
            },
            'export_timestamp': self._get_timestamp()
        }
    
    def __str__(self) -> str:
        """Representación string de Lucy AI"""
        return (f"LucyAI(language={self.current_language}, "
                f"context={len(self.conversation_context)}, "
                f"model={'loaded' if self.model else 'not loaded'})")
    
    def __repr__(self) -> str:
        """Representación detallada de Lucy AI"""
        return (f"LucyAI(current_language='{self.current_language}', "
                f"supported_languages={list(self.intents.keys())}, "
                f"model_loaded={self.model is not None}, "
                f"vocabulary_size={len(self.words) if self.words else 0}, "
                f"context_length={len(self.conversation_context)})")