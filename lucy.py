import os
import random
import json
import pickle
import numpy as np
import sys

# Configuración de entorno para suprimir mensajes
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.stderr = open(os.devnull, 'w')

from utils import get_language, suppress_tf_logs
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model

# =============================================
# CONFIGURACIÓN DE RUTAS (AJUSTADO A TU ESTRUCTURA)
# =============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "core")  # Cambiado porque tus archivos están en /core
MODELS_DIR = os.path.join(BASE_DIR, "models")

# =============================================
# CARGA DE MODELOS Y DATOS (CON MANEJO DE ERRORES)
# =============================================
try:
    with suppress_tf_logs():
        lemmatizer = WordNetLemmatizer()
        
        # Verificar existencia de archivos
        required_files = {
            'words': os.path.join(DATA_DIR, "words.pkl"),
            'classes': os.path.join(DATA_DIR, "classes.pkl"),
            'model': os.path.join(MODELS_DIR, "lucy_model.h5"),
            'intents_es': os.path.join(DATA_DIR, "intents_es.json"),
            'intents_en': os.path.join(DATA_DIR, "intents_en.json")
        }
        
        for name, path in required_files.items():
            if not os.path.exists(path):
                print(f"Error: Archivo no encontrado - {path}")
        
        words = pickle.load(open(required_files['words'], 'rb'))
        classes = pickle.load(open(required_files['classes'], 'rb'))
        model = load_model(required_files['model'])
        model.make_predict_function()

except Exception as e:
    print(f"Error al cargar recursos: {str(e)}")
    sys.exit(1)

# =============================================
# FUNCIONES PRINCIPALES
# =============================================
def clean_up_sentence(sentence):
    """Limpia y lematiza la oración"""
    sentence_words = nltk.word_tokenize(sentence)
    return [lemmatizer.lemmatize(word.lower()) for word in sentence_words]

def bag_of_words(sentence):
    """Crea la bolsa de palabras"""
    sentence_words = clean_up_sentence(sentence)
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, word in enumerate(words):
        if word in sentence_words:
            bag[idx] = 1
    return bag

def predict_class(sentence):
    """Predice la categoría del mensaje"""
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]), verbose=0)[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return [{"intent": classes[r[0]], "probability": str(r[1])} for r in results]

def get_response(intents_list, intents_json, lang="es"):
    if not intents_list:
        return "No entendí eso" if lang == "es" else "I didn't understand that"
    
    tag = intents_list[0]['intent']
    for i in intents_json['intents']:
        if i['tag'] == tag:
            return random.choice(i['responses'])
    return "No tengo una respuesta para eso" if lang == "es" else "I don't have a response for that"

def chat():
    print("\nLucy: Hola! Soy Lucy, tu asistente. ¿En qué puedo ayudarte?")
    print("Lucy: Hi! I'm Lucy, your assistant. How can I help you?")
    print("(Escribe 'salir' o 'exit' para terminar)\n")
    
    while True:
        try:
            message = input("Tú: ")
            
            if message.lower() in ['salir', 'exit', 'quit']:
                print("\nLucy: Hasta pronto! // Goodbye!")
                break
                
            lang = get_language(message)
            intents_file = os.path.join(DATA_DIR, f"intents_{lang}.json")
            
            if not os.path.exists(intents_file):
                print(f"Lucy: Error - Archivo {intents_file} no encontrado")
                continue
                
            with open(intents_file, 'r', encoding='utf-8') as file:
                current_intents = json.load(file)
                
            ints = predict_class(message)
            res = get_response(ints, current_intents, lang)
            print(f"Lucy: {res}")
                
        except KeyboardInterrupt:
            print("\nLucy: Sesión interrumpida // Session interrupted")
            break
        except Exception as e:
            print(f"Lucy: Error inesperado // Unexpected error: {str(e)}")

if __name__ == "__main__":
    chat()
# =============================================
# EJECUCIÓN PRINCIPAL
# =============================================
if __name__ == "__main__":
    # Verificar recursos necesarios
    required_files = [
        os.path.join(DATA_DIR, "words.pkl"),
        os.path.join(DATA_DIR, "classes.pkl"),
        os.path.join(MODELS_DIR, "lucy_model.h5"),
        os.path.join(DATA_DIR, "intents_es.json"),
        os.path.join(DATA_DIR, "intents_en.json")
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("Error: Archivos necesarios no encontrados:")
        for f in missing_files:
            print(f"- {f}")
        sys.exit(1)
    
    # Iniciar chat
    chat()