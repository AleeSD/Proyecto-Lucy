# Lucy AI - Asistente de IA Conversacional

Un asistente de inteligencia artificial conversacional que aprende del usuario, desarrollado en Python con TensorFlow y NLTK.

## 🚀 Características

- **Procesamiento de Lenguaje Natural**: Utiliza NLTK y TensorFlow para entender y responder mensajes
- **Multilingüe**: Soporte para español e inglés
- **Aprendizaje Automático**: Modelo de red neuronal para clasificación de intenciones
- **Base de Datos**: Almacenamiento persistente de conversaciones y contexto
- **Interfaz Interactiva**: Chat en línea de comandos con comandos especiales
- **Sistema de Logging**: Registro detallado de actividades y errores
- **Configuración Flexible**: Archivo JSON para personalizar comportamiento

## 📋 Requisitos

- Python 3.8 o superior
- Windows, Linux o macOS
- Conexión a internet (para descargar datos de NLTK)

## 🛠️ Instalación Rápida

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd Proyecto-Lucy
```

### 2. Crear entorno virtual
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Preparación automática (opcional)
Usa los scripts de preparación para automatizar entorno virtual, dependencias y datos NLTK:
```bash
# Windows (PowerShell)
scripts\setup_env.ps1

# Linux/Mac
bash scripts/setup_env.sh
```

## 🎯 Uso

### Modo Interactivo
```bash
python lucy.py
```

### Ejecutar Tests y Cobertura
```bash
pytest -q --cov=src/lucy --cov-report=term-missing
```

### Scripts de Lanzamiento
```bash
# Windows
run_lucy.bat

# Linux/Mac
./run_lucy.sh
```

### Prueba Rápida
```bash
pytest -q
```

## 💬 Comandos Especiales

Una vez en el chat interactivo, puedes usar estos comandos:

- `/help` - Mostrar ayuda
- `/config` - Ver configuración actual
- `/stats` - Ver estadísticas de sesión
- `/clear` - Limpiar contexto de conversación
- `/debug` - Información de debug
- `/exit` - Salir del programa

## 📁 Estructura del Proyecto

```
Proyecto-Lucy/
├── lucy.py                 # Punto de entrada principal (CLI)
├── requirements.txt        # Dependencias del proyecto
├── src/
│   └── lucy/               # Paquete principal
│       ├── __init__.py
│       ├── lucy_ai.py         # Motor de IA principal
│       ├── config_manager.py  # Gestor de configuración dinámico
│       ├── database.py        # Base de datos SQLite
│       ├── logging_system.py  # Sistema de logging y monitoreo
│       ├── training.py        # Sistema de entrenamiento
│       └── utils.py           # Utilidades generales
├── core/                  # Capa de compatibilidad (reexporta desde src/lucy)
│   ├── __init__.py
│   ├── lucy_ai.py
│   ├── config_manager.py
│   ├── database.py
│   ├── logging_system.py
│   ├── training.py
│   └── utils.py
├── config/
│   ├── config.json        # Configuración del sistema
│   └── logging.yaml       # Configuración avanzada de logs
├── data/
│   ├── intents/           # Archivos de intenciones
│   │   ├── intents_es.json
│   │   └── intents_en.json
│   └── models/            # Modelos entrenados
├── logs/                  # Archivos de log
└── tests/                 # Tests unitarios
```

Nota: `core/` se mantiene temporalmente como alias para asegurar compatibilidad con código y tests existentes. Se recomienda migrar a imports desde `lucy.*`.

## ⚙️ Configuración

El archivo `config/config.json` permite personalizar:

- **Idioma por defecto**: `es` o `en`
- **Umbral de confianza**: 0.0 a 1.0
- **Rutas de archivos**: Directorios de datos, modelos, logs
- **Logging**: Nivel de detalle y archivos de salida
- **Base de datos**: Configuración de SQLite

## 🧠 Entrenamiento

### Re-entrenar el modelo
```bash
python -m src.lucy.training --force
```

### Entrenar con parámetros específicos
```bash
python -m src.lucy.training --epochs 300 --batch-size 10
```

### Validar modelo existente
```bash
python -m src.lucy.training --validate
```

Optimización (Día 3):
- EarlyStopping y ReduceLROnPlateau habilitados por defecto.
- Guardado del mejor modelo y checkpoints por época en `data/models/`.
- Historial CSV en `data/models/training_log.csv`.
- Semillas fijadas para mayor reproducibilidad.

## 🔧 Desarrollo

### Ejecutar tests
```bash
python lucy.py --test
```

### Modo debug
```bash
python lucy.py --debug
```

### Optimizar proyecto
```bash
python optimize_project.py
```

## 📊 Monitoreo

- **Logs**: `logs/lucy.log`
- **Base de datos**: `data/conversations.db`
- **Estadísticas**: Comando `/stats` en el chat

## 🐛 Solución de Problemas

### Error de codificación en Windows
Si ves errores de `charmap`, el proyecto ya está configurado para usar UTF-8 automáticamente.

### Modelo no encontrado
Si no tienes un modelo entrenado, Lucy funcionará en modo básico usando los archivos de intenciones.

### Dependencias faltantes
```bash
pip install -r requirements.txt
```

### Datos NLTK faltantes
Se descargan automáticamente al iniciar, pero puedes descargarlos manualmente:
```python
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
```

### Modelos o intents ausentes
- Si faltan archivos en `data/models/`, Lucy funciona en modo básico sin ML.
- Asegúrate de que existan `data/intents/intents_es.json` y `data/intents/intents_en.json`.

## 📚 Documentación ampliada (Día 7)
- Guía de instalación: `docs/Guia_Instalacion.md`
- Guía de ejecución: `docs/Guia_Ejecucion.md`
- Guía de deployment: `docs/Guia_Deployment.md`
 - Registro del día: `docs/Dia_07_Documentacion_Deployment.md`

## 📈 Próximas Características

- [ ] API REST para integración web
- [ ] Interfaz gráfica (GUI)
- [ ] Reconocimiento de voz
- [ ] Síntesis de voz
- [ ] Integración con servicios externos
- [ ] Plugins personalizables
- [ ] Análisis de sentimientos
- [ ] Aprendizaje continuo

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**AleeSD** - [GitHub](https://github.com/AleeSD)

## 🙏 Agradecimientos

- TensorFlow por el framework de ML
- NLTK por el procesamiento de lenguaje natural
- La comunidad de Python por las librerías utilizadas

---

**¡Disfruta conversando con Lucy! 🤖**