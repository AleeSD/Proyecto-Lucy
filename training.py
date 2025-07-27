import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Ocultar mensajes de TensorFlow

import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.optimizers import SGD

# Preprocesamiento de datos (tokenización, lematización, etc.)
lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents.json').read())

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')

words = []
classes = []
documents = []
ignore_letters = ['?', '¿', '¡', '!', '.', ',', "'"]

for intent in intents['intents']:
    for pattern in intent['patterns']:
        word_list = nltk.word_tokenize(pattern)
        words.extend(word_list)
        documents.append((word_list, intent['tag']))
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

words = [lemmatizer.lemmatize(word) for word in words if word not in ignore_letters]
words = sorted(set(words))

pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

# Preparación de los datos de entrenamiento
training = []
output_empty = [0] * len(classes)

for document in documents:
    bag = []
    word_patterns = document[0]
    word_patterns = [lemmatizer.lemmatize(word.lower()) for word in word_patterns]
    for word in words:
        bag.append(1) if word in word_patterns else bag.append(0)
    output_row = list(output_empty)
    output_row[classes.index(document[1])] = 1
    training.append([bag, output_row])

random.shuffle(training)

# Separar en X (entradas) y y (etiquetas)
train_x = np.array([item[0] for item in training])
train_y = np.array([item[1] for item in training])

# Paso 5: Crear y entrenar el modelo de Keras
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

model.compile(optimizer=SGD(), loss='categorical_crossentropy', metrics=['accuracy'])
# Modificar la línea del model.fit para ocultar progreso
model.fit(train_x, train_y, epochs=200, batch_size=5, verbose=0)
# Guardar el modelo entrenado
model.save('lucy_model.h5')
print("Modelo entrenado y guardado.")