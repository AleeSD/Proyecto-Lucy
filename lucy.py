import random
import json
import pickle
import numpy as np
import os
import sys

# Configurar entorno para suprimir mensajes de TensorFlow/Keras
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import load_model

sys.stderr = stderr  # Restaurar stderr

lemmatizer = WordNetLemmatizer()

# Cargar intents con codificación UTF-8 para soportar caracteres especiales
with open('intents.json', 'r', encoding='utf-8') as file:
    intents = json.load(file)

words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))

# Cargar modelo silenciosamente
model = load_model('lucy_model.h5')
model.make_predict_function()  # Para evitar mensajes de TensorFlow

from utils import suppress_tf_logs

with suppress_tf_logs():
    model = load_model('lucy_model.h5')

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    res = model.predict(np.array([bow]), verbose=0)[0]  # verbose=0 para silenciar
    max_index = np.where(res == np.max(res))[0][0]
    category = classes[max_index]
    return category

def get_response(tag, intents_json):
    list_of_intents = intents_json['intents']
    result = ""
    for i in list_of_intents:
        if i['tag'] == tag:
            result = random.choice(i['responses'])
            break
    # Limpieza más agresiva de caracteres
    return result.replace('Â', '').replace('Ã¡', 'á').replace('Ã±', 'ñ').replace('Ã©', 'é')

# Configurar la salida estándar para UTF-8
sys.stdout.reconfigure(encoding='utf-8')

print("Lucy está lista. Escribe tu mensaje:")

while True:
    try:
        message = input("> ")
        ints = predict_class(message)
        res = get_response(ints, intents)
        print(res)
    except KeyboardInterrupt:
        print("\nHasta pronto!")
        break
    except Exception as e:
        print("Lo siento, ocurrió un error. Intenta de nuevo.")