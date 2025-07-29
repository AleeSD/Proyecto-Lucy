from core.language_utils import detect_language

class LucyAI:
    def __init__(self):
        self.language = 'es'  # Idioma por defecto
    
    def process_input(self, text):
        self.language = detect_language(text)
        # Aquí puedes agregar la lógica para manejar la entrada según el idioma detectado
