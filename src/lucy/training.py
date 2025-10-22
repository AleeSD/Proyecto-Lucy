"""
Sistema de Entrenamiento para Lucy AI
====================================

Maneja el entrenamiento del modelo de machine learning, 
procesamiento de intenciones y optimización del modelo.
"""

import os
import json
import pickle
import random
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any
import random as pyrandom

# Configurar TensorFlow antes de importar
from .utils import suppress_tf_logs, load_json_file, measure_execution_time
from .logging_system import log_performance
from .config_manager import get_config_manager

# Importaciones con supresión de logs
with suppress_tf_logs():
    import nltk
    from nltk.stem import WordNetLemmatizer
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Activation, Dropout
    from tensorflow.keras.optimizers import SGD
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, CSVLogger
    from sklearn.model_selection import train_test_split


class LucyTrainer:
    """Sistema de entrenamiento para Lucy AI"""
    
    def __init__(self, config_manager=None):
        """
        Inicializa el sistema de entrenamiento
        
        Args:
            config_manager: Gestor de configuración (opcional)
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager or get_config_manager()
        self.config = self.config_manager.get_all()
        
        # Configuración del entrenamiento
        self.epochs = self.config.get('model', {}).get('training_epochs', 200)
        self.batch_size = self.config.get('model', {}).get('batch_size', 5)
        self.dropout_rate = self.config.get('model', {}).get('dropout_rate', 0.5)
        self.validation_split = self.config.get('training', {}).get('validation_split', 0.2)
        self.seed = int(self.config.get('training', {}).get('seed', 42))
        self.enable_early_stopping = bool(self.config.get('training', {}).get('early_stopping', True))
        self.enable_lr_schedule = bool(self.config.get('training', {}).get('reduce_lr_on_plateau', True))
        self.enable_csv_logger = bool(self.config.get('training', {}).get('csv_logger', True))
        
        # Componentes del modelo
        self.lemmatizer = WordNetLemmatizer()
        self.words = []
        self.classes = []
        self.documents = []
        self.ignore_words = ['?', '¿', '¡', '!', '.', ',', "'", '"', ':', ';']
        
        # Paths
        self.data_paths = self._setup_paths()
        
        # Asegurar datos de NLTK
        self._ensure_nltk_data()
        self._set_global_seeds()
        
        self.logger.info("[OK] Sistema de entrenamiento inicializado")
    
    def _setup_paths(self) -> Dict[str, Path]:
        """Configura las rutas necesarias para el entrenamiento"""
        paths = {
            'intents_dir': Path(self.config_manager.get_path('intents_dir')),
            'models_dir': Path(self.config_manager.get_path('models_dir')),
            'words_file': Path(self.config_manager.get_path('models_dir')) / 'words.pkl',
            'classes_file': Path(self.config_manager.get_path('models_dir')) / 'classes.pkl',
            'model_file': Path(self.config_manager.get_path('models_dir')) / 'lucy_model.h5'
        }
        
        # Crear directorios si no existen
        paths['models_dir'].mkdir(parents=True, exist_ok=True)
        
        return paths
    
    def _ensure_nltk_data(self):
        """Asegura que los datos de NLTK estén disponibles"""
        try:
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

    def _set_global_seeds(self):
        """Fija semillas para reproducibilidad básica"""
        try:
            np.random.seed(self.seed)
            pyrandom.seed(self.seed)
            with suppress_tf_logs():
                import tensorflow as tf
                tf.random.set_seed(self.seed)
            self.logger.debug(f"[OK] Semillas fijadas: {self.seed}")
        except Exception as e:
            self.logger.warning(f"No se pudieron fijar semillas completamente: {e}")
    
    @measure_execution_time
    def load_training_data(self, languages: List[str] = None) -> bool:
        """
        Carga los datos de entrenamiento desde archivos de intenciones
        
        Args:
            languages: Lista de idiomas a procesar (None para todos)
            
        Returns:
            True si se cargaron datos exitosamente
        """
        try:
            self.logger.info("[REFRESH] Cargando datos de entrenamiento...")
            
            # Resetear datos
            self.words = []
            self.classes = []
            self.documents = []
            
            # Idiomas a procesar
            if languages is None:
                languages = self.config.get('model', {}).get('supported_languages', ['es', 'en'])
            
            total_patterns = 0
            total_intents = 0
            
            for language in languages:
                intent_file = self.data_paths['intents_dir'] / f'intents_{language}.json'
                
                if not intent_file.exists():
                    self.logger.warning(f"[WARN] Archivo no encontrado: {intent_file}")
                    continue
                
                # Cargar intenciones
                intents_data = load_json_file(str(intent_file))
                if not intents_data or 'intents' not in intents_data:
                    self.logger.warning(f"[WARN] Datos inválidos en: {intent_file}")
                    continue
                
                # Procesar cada intención
                for intent in intents_data['intents']:
                    tag = intent.get('tag')
                    patterns = intent.get('patterns', [])
                    
                    if not tag or not patterns:
                        continue
                    
                    # Agregar clase si no existe
                    if tag not in self.classes:
                        self.classes.append(tag)
                    
                    # Procesar cada patrón
                    for pattern in patterns:
                        # Tokenizar patrón
                        word_list = nltk.word_tokenize(pattern.lower())
                        self.words.extend(word_list)
                        self.documents.append((word_list, tag))
                        total_patterns += 1
                    
                    total_intents += 1
                
                self.logger.info(f"[OK] Cargado {language}: {len(intents_data['intents'])} intenciones")
            
            if not self.documents:
                raise ValueError("No se encontraron datos de entrenamiento válidos")
            
            # Procesar vocabulario
            self.words = [self.lemmatizer.lemmatize(word.lower()) 
                        for word in self.words if word not in self.ignore_words]
            self.words = sorted(list(set(self.words)))
            self.classes = sorted(self.classes)
            
            self.logger.info(f"[OK] Datos cargados: {total_patterns} patrones, "
                        f"{total_intents} intenciones, {len(self.words)} palabras únicas")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cargando datos: {e}")
            return False
    
    @measure_execution_time
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara los datos para el entrenamiento del modelo
        
        Returns:
            Tupla con datos de entrada (X) y etiquetas (y)
        """
        try:
            self.logger.info("🔄 Preparando datos de entrenamiento...")
            
            training = []
            output_empty = [0] * len(self.classes)
            
            # Crear datos de entrenamiento
            for document in self.documents:
                bag = []
                word_patterns = document[0]
                
                # Lematizar patrones de palabras
                word_patterns = [self.lemmatizer.lemmatize(word.lower()) 
                            for word in word_patterns]
                
                # Crear bolsa de palabras
                for word in self.words:
                    bag.append(1) if word in word_patterns else bag.append(0)
                
                # Crear vector de salida
                output_row = list(output_empty)
                output_row[self.classes.index(document[1])] = 1
                
                training.append([bag, output_row])
            
            # Mezclar datos
            random.shuffle(training)
            
            # Separar características y etiquetas
            train_x = np.array([item[0] for item in training])
            train_y = np.array([item[1] for item in training])
            
            self.logger.info(f"✅ Datos preparados: {train_x.shape[0]} muestras, "
                        f"{train_x.shape[1]} características")
            
            return train_x, train_y
            
        except Exception as e:
            self.logger.error(f"Error preparando datos: {e}")
            raise
    
    def create_model(self, input_size: int, output_size: int) -> Sequential:
        """
        Crea el modelo de red neuronal
        
        Args:
            input_size: Tamaño de entrada (vocabulario)
            output_size: Tamaño de salida (clases)
            
        Returns:
            Modelo de Keras
        """
        try:
            self.logger.info("🔄 Creando modelo de red neuronal...")
            
            model = Sequential([
                Dense(128, input_shape=(input_size,), activation='relu'),
                Dropout(self.dropout_rate),
                Dense(64, activation='relu'),
                Dropout(self.dropout_rate),
                Dense(output_size, activation='softmax')
            ])
            
            # Configurar optimizador
            learning_rate = float(self.config.get('training', {}).get('learning_rate', 0.01))
            optimizer = SGD(learning_rate=learning_rate, momentum=0.9, nesterov=True)
            
            # Compilar modelo
            model.compile(
                optimizer=optimizer,
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            
            self.logger.info("✅ Modelo creado y compilado")
            self.logger.info(f"   - Capas: {len(model.layers)}")
            self.logger.info(f"   - Parámetros: {model.count_params()}")
            self.logger.info(f"   - LR inicial: {learning_rate}")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Error creando modelo: {e}")
            raise
    
    @measure_execution_time
    def train_model(self, model: Sequential, train_x: np.ndarray, 
                train_y: np.ndarray, validation_data: Tuple = None) -> Dict[str, Any]:
        """
        Entrena el modelo de red neuronal
        
        Args:
            model: Modelo de Keras a entrenar
            train_x: Datos de entrada
            train_y: Etiquetas
            validation_data: Datos de validación (opcional)
            
        Returns:
            Historial de entrenamiento
        """
        try:
            self.logger.info("🧠 Iniciando entrenamiento del modelo...")
            self.logger.info(f"   - Épocas: {self.epochs}")
            self.logger.info(f"   - Batch size: {self.batch_size}")
            self.logger.info(f"   - Dropout: {self.dropout_rate}")
            
            # Configurar callbacks si está habilitado
            callbacks = []
            
            if self.config.get('training', {}).get('save_checkpoints', True):
                from tensorflow.keras.callbacks import ModelCheckpoint
                checkpoint_path = self.data_paths['models_dir'] / 'checkpoint_{epoch:02d}.h5'
                checkpoint = ModelCheckpoint(
                    str(checkpoint_path),
                    save_best_only=True,
                    monitor='val_loss' if validation_data else 'loss',
                    mode='min'
                )
                callbacks.append(checkpoint)

            # EarlyStopping
            if self.enable_early_stopping:
                patience = int(self.config.get('training', {}).get('early_stopping_patience', 10))
                es = EarlyStopping(
                    monitor='val_loss' if validation_data else 'loss',
                    mode='min',
                    patience=patience,
                    restore_best_weights=True
                )
                callbacks.append(es)

            # ReduceLROnPlateau
            if self.enable_lr_schedule:
                factor = float(self.config.get('training', {}).get('reduce_lr_factor', 0.5))
                patience_rlr = int(self.config.get('training', {}).get('reduce_lr_patience', 5))
                min_lr = float(self.config.get('training', {}).get('reduce_lr_min', 1e-5))
                rlr = ReduceLROnPlateau(
                    monitor='val_loss' if validation_data else 'loss',
                    mode='min',
                    factor=factor,
                    patience=patience_rlr,
                    min_lr=min_lr,
                    verbose=1
                )
                callbacks.append(rlr)

            # CSV Logger
            if self.enable_csv_logger:
                csv_path = self.data_paths['models_dir'] / 'training_log.csv'
                csv_logger = CSVLogger(str(csv_path), append=False)
                callbacks.append(csv_logger)
            
            # Entrenar modelo
            with suppress_tf_logs():
                history = model.fit(
                    train_x, train_y,
                    epochs=self.epochs,
                    batch_size=self.batch_size,
                    validation_data=validation_data,
                    callbacks=callbacks,
                    verbose=1 if self.logger.level <= logging.INFO else 0
                )
            
            # Evaluar modelo final (en conjunto de entrenamiento)
            final_loss, final_accuracy = model.evaluate(train_x, train_y, verbose=0)
            
            self.logger.info(f"✅ Entrenamiento completado:")
            self.logger.info(f"   - Pérdida final: {final_loss:.4f}")
            self.logger.info(f"   - Precisión final: {final_accuracy:.4f}")
            
            return {
                'history': history.history,
                'final_loss': final_loss,
                'final_accuracy': final_accuracy,
                'epochs_completed': len(history.history['loss'])
            }
            
        except Exception as e:
            self.logger.error(f"Error en entrenamiento: {e}")
            raise
    
    def save_model_components(self, model: Sequential) -> bool:
        """
        Guarda el modelo y sus componentes
        
        Args:
            model: Modelo entrenado a guardar
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            self.logger.info("💾 Guardando modelo y componentes...")
            
            # Guardar vocabulario
            with open(self.data_paths['words_file'], 'wb') as f:
                pickle.dump(self.words, f)
            
            # Guardar clases
            with open(self.data_paths['classes_file'], 'wb') as f:
                pickle.dump(self.classes, f)
            
            # Guardar modelo
            with suppress_tf_logs():
                model.save(str(self.data_paths['model_file']))
            
            self.logger.info("✅ Modelo guardado exitosamente:")
            self.logger.info(f"   - Vocabulario: {self.data_paths['words_file']}")
            self.logger.info(f"   - Clases: {self.data_paths['classes_file']}")
            self.logger.info(f"   - Modelo: {self.data_paths['model_file']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error guardando modelo: {e}")
            return False
    
    def validate_model(self, model: Sequential, train_x: np.ndarray, 
                    train_y: np.ndarray) -> Dict[str, Any]:
        """
        Valida el modelo entrenado
        
        Args:
            model: Modelo a validar
            train_x: Datos de entrada
            train_y: Etiquetas
            
        Returns:
            Métricas de validación
        """
        try:
            self.logger.info("🔍 Validando modelo...")
            
            # Predicciones
            with suppress_tf_logs():
                predictions = model.predict(train_x, verbose=0)
            
            # Calcular métricas
            predicted_classes = np.argmax(predictions, axis=1)
            true_classes = np.argmax(train_y, axis=1)
            
            # Accuracy
            accuracy = np.mean(predicted_classes == true_classes)
            
            # Confianza promedio
            avg_confidence = np.mean(np.max(predictions, axis=1))
            
            # Distribución de confianzas
            confidence_threshold = self.config.get('model', {}).get('confidence_threshold', 0.25)
            high_confidence_count = np.sum(np.max(predictions, axis=1) >= confidence_threshold)
            
            validation_results = {
                'accuracy': accuracy,
                'average_confidence': avg_confidence,
                'high_confidence_predictions': high_confidence_count,
                'total_predictions': len(predictions),
                'high_confidence_ratio': high_confidence_count / len(predictions),
                'classes_count': len(self.classes),
                'vocabulary_size': len(self.words)
            }
            
            self.logger.info("✅ Validación completada:")
            for key, value in validation_results.items():
                if isinstance(value, float):
                    self.logger.info(f"   - {key}: {value:.4f}")
                else:
                    self.logger.info(f"   - {key}: {value}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error en validación: {e}")
            return {'error': str(e)}
    
    def run_full_training(self, languages: List[str] = None, 
                        force_retrain: bool = False) -> bool:
        """
        Ejecuta el proceso completo de entrenamiento
        
        Args:
            languages: Idiomas a entrenar (None para todos)
            force_retrain: Forzar re-entrenamiento aunque exista modelo
            
        Returns:
            True si el entrenamiento fue exitoso
        """
        try:
            # Verificar si ya existe un modelo
            if not force_retrain and self.data_paths['model_file'].exists():
                self.logger.info("ℹ️ Modelo existente encontrado. Use force_retrain=True para re-entrenar")
                return True
            
            self.logger.info("🚀 Iniciando entrenamiento completo...")
            
            # 1. Cargar datos
            if not self.load_training_data(languages):
                return False
            
            # 2. Preparar datos
            train_x, train_y = self.prepare_training_data()
            
            # 3. Dividir en entrenamiento y validación
            validation_data = None
            if self.validation_split > 0:
                train_x, val_x, train_y, val_y = train_test_split(
                    train_x, train_y, 
                    test_size=self.validation_split, 
                    random_state=42
                )
                validation_data = (val_x, val_y)
                self.logger.info(f"📊 División de datos: "
                            f"{len(train_x)} entrenamiento, {len(val_x)} validación")
            
            # 4. Crear modelo
            model = self.create_model(len(train_x[0]), len(train_y[0]))
            
            # 5. Entrenar modelo
            training_results = self.train_model(model, train_x, train_y, validation_data)
            # Emitir métricas al sistema de logging (tiempo total de entrenamiento, si disponible)
            try:
                if 'history' in training_results and 'loss' in training_results['history']:
                    epochs_completed = training_results.get('epochs_completed', len(training_results['history']['loss']))
                    final_loss = float(training_results.get('final_loss', 0.0))
                    final_acc = float(training_results.get('final_accuracy', 0.0))
                    log_performance('training.epochs_completed', epochs_completed, unit='epochs')
                    log_performance('training.final_loss', final_loss)
                    log_performance('training.final_accuracy', final_acc)
            except Exception:
                pass
            
            # 6. Validar modelo
            validation_results = self.validate_model(model, train_x, train_y)
            try:
                if 'accuracy' in validation_results:
                    log_performance('validation.accuracy', float(validation_results['accuracy']))
                if 'average_confidence' in validation_results:
                    log_performance('validation.avg_confidence', float(validation_results['average_confidence']))
            except Exception:
                pass
            
            # 7. Guardar modelo
            if not self.save_model_components(model):
                return False
            
            # 8. Generar reporte
            self._generate_training_report(training_results, validation_results)
            
            self.logger.info("🎉 Entrenamiento completado exitosamente!")
            return True
            
        except Exception as e:
            self.logger.error(f"Error en entrenamiento completo: {e}")
            return False
    
    def _generate_training_report(self, training_results: Dict[str, Any], 
                                validation_results: Dict[str, Any]):
        """
        Genera un reporte del entrenamiento
        
        Args:
            training_results: Resultados del entrenamiento
            validation_results: Resultados de validación
        """
        try:
            report = {
                'timestamp': self._get_timestamp(),
                'configuration': {
                    'epochs': self.epochs,
                    'batch_size': self.batch_size,
                    'dropout_rate': self.dropout_rate,
                    'validation_split': self.validation_split
                },
                'data_statistics': {
                    'total_words': len(self.words),
                    'total_classes': len(self.classes),
                    'total_documents': len(self.documents)
                },
                'training_results': training_results,
                'validation_results': validation_results
            }
            
            # Guardar reporte
            report_path = self.data_paths['models_dir'] / 'training_report.json'
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 Reporte guardado: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error generando reporte: {e}")
    
    def _get_timestamp(self) -> str:
        """Obtiene timestamp actual en formato ISO"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_training_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del estado actual del entrenador
        
        Returns:
            Estadísticas del entrenamiento
        """
        return {
            'words_count': len(self.words),
            'classes_count': len(self.classes),
            'documents_count': len(self.documents),
            'configuration': {
                'epochs': self.epochs,
                'batch_size': self.batch_size,
                'dropout_rate': self.dropout_rate,
                'validation_split': self.validation_split
            },
            'files_exist': {
                'words': self.data_paths['words_file'].exists(),
                'classes': self.data_paths['classes_file'].exists(),
                'model': self.data_paths['model_file'].exists()
            }
        }


def main():
    """Función principal para ejecutar el entrenamiento desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Entrenamiento de Lucy AI")
    parser.add_argument('--languages', nargs='+', default=None,
                    help='Idiomas a entrenar (ej: es en)')
    parser.add_argument('--force', action='store_true',
                    help='Forzar re-entrenamiento')
    parser.add_argument('--config', type=str, default=None,
                    help='Archivo de configuración personalizado')
    parser.add_argument('--epochs', type=int, default=None,
                    help='Número de épocas de entrenamiento')
    parser.add_argument('--batch-size', type=int, default=None,
                    help='Tamaño de batch')
    parser.add_argument('--validate', action='store_true',
                    help='Solo validar modelo existente')
    
    args = parser.parse_args()
    
    try:
        # Configurar logging para CLI
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Inicializar entrenador
        config_manager = get_config_manager(args.config) if args.config else None
        trainer = LucyTrainer(config_manager)
        
        # Aplicar parámetros de línea de comandos
        if args.epochs:
            trainer.epochs = args.epochs
        if args.batch_size:
            trainer.batch_size = args.batch_size
        
        if args.validate:
            # Solo validar modelo existente
            print("🔍 Validando modelo existente...")
            
            # Verificar que existe el modelo
            if not trainer.data_paths['model_file'].exists():
                print("❌ No se encontró modelo para validar")
                return False
            
            # Cargar datos y validar
            trainer.load_training_data(args.languages)
            train_x, train_y = trainer.prepare_training_data()
            
            # Cargar modelo existente
            with suppress_tf_logs():
                from tensorflow.keras.models import load_model
                model = load_model(str(trainer.data_paths['model_file']))
            
            # Validar
            results = trainer.validate_model(model, train_x, train_y)
            print("✅ Validación completada")
            
            return True
        
        else:
            # Entrenamiento completo
            success = trainer.run_full_training(
                languages=args.languages,
                force_retrain=args.force
            )
            
            if success:
                print("🎉 ¡Entrenamiento exitoso!")
                return True
            else:
                print("❌ Error en el entrenamiento")
                return False
    
    except KeyboardInterrupt:
        print("\n⏹️ Entrenamiento interrumpido por el usuario")
        return False
    
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)