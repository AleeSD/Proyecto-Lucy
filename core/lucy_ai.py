"""Compatibilidad: reexporta lucy.lucy_ai y expone load_model para tests"""
# Asegurar que paquete lucy bajo `src/` esté en sys.path
import sys
from pathlib import Path
_src_dir = str(Path(__file__).resolve().parents[1] / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Exponer load_model a nivel de módulo para compatibilidad con tests
try:
    from tensorflow.keras.models import load_model as _tf_load_model  # type: ignore
except Exception:
    def _tf_load_model(*args, **kwargs):
        raise RuntimeError("TensorFlow/Keras no disponible")
load_model = _tf_load_model

# Reexportar API principal
from lucy.lucy_ai import *