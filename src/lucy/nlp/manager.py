"""
Gestor de PLN Avanzado (Día 10)
================================

Provee análisis ligero de texto: sentimiento, entidades y palabras clave
sin dependencias externas pesadas.
"""

import re
from collections import Counter
from typing import Any, Dict, List

from ..config_manager import ConfigManager


class AdvancedNLPManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        cfg = config_manager.get("advanced_nlp", {}) or {}
        self.enabled = bool(cfg.get("enabled", True))
        kw_cfg = cfg.get("keywords", {}) or {}
        self.top_n = int(kw_cfg.get("top_n", 5))
        # Listas mínimas de stopwords ES/EN
        self.stopwords = set([
            # Español
            "y", "de", "la", "el", "en", "que", "a", "los", "las", "un", "una",
            "por", "con", "para", "como", "es", "no", "si", "del", "al",
            # Inglés
            "and", "the", "is", "in", "of", "to", "a", "an", "for", "on", "with",
            "that", "this", "it", "at"
        ])
        # Lexicon simple
        self.pos_words = set(["bueno", "excelente", "genial", "feliz", "alegre", "positivo", "great", "good", "happy", "awesome"])
        self.neg_words = set(["malo", "terrible", "triste", "negativo", "horrible", "fatal", "bad", "sad", "awful", "worse"])

    def analyze(self, text: str) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False}
        if not text:
            return {"sentiment": {"score": 0.0, "label": "neutral"}, "entities": {}, "keywords": []}

        tokens = self._tokenize(text)
        content_tokens = [t for t in tokens if t.lower() not in self.stopwords]

        # Sentimiento
        pos = sum(1 for t in content_tokens if t.lower() in self.pos_words)
        neg = sum(1 for t in content_tokens if t.lower() in self.neg_words)
        denom = max(len(content_tokens), 1)
        score = (pos - neg) / denom
        label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"

        # Entidades simples
        entities = {
            "emails": re.findall(r"[\w\.\-]+@[\w\.-]+", text),
            "dates": re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text),
            "numbers": re.findall(r"\b\d+(?:\.\d+)?\b", text),
        }

        # Palabras clave
        freq = Counter([t.lower() for t in content_tokens if t.isalpha()])
        keywords = [w for w, _ in freq.most_common(self.top_n)]

        return {
            "sentiment": {"score": round(score, 4), "label": label, "pos": pos, "neg": neg},
            "entities": entities,
            "keywords": keywords,
        }

    def _tokenize(self, text: str) -> List[str]:
        # Tokenización simple por separadores no alfanuméricos
        return [t for t in re.split(r"[^\wáéíóúÁÉÍÓÚ]+", text) if t]