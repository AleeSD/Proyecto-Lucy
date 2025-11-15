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
from .pipelines import (
    analyze_document_sentiment,
    analyze_sentence_sentiment,
    generate_text,
    translate_text,
    extract_entities,
    extract_relations,
)


class AdvancedNLPManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        cfg = config_manager.get("advanced_nlp", {}) or {}
        self.enabled = bool(cfg.get("enabled", True))
        kw_cfg = cfg.get("keywords", {}) or {}
        self.top_n = int(kw_cfg.get("top_n", 5))
        self.transformers_enabled = bool(cfg.get("transformers_enabled", False))
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

        # Entidades mejoradas
        entities = extract_entities(text)

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

    # --- Capacidades avanzadas ---
    def analyze_sentiment_doc(self, text: str) -> Dict[str, Any]:
        return analyze_document_sentiment(text)

    def analyze_sentiment_sentence(self, text: str) -> List[Dict[str, Any]]:
        return analyze_sentence_sentiment(text)

    def named_entity_recognition(self, text: str) -> Dict[str, Any]:
        return extract_entities(text)

    def relation_extraction(self, text: str) -> List[Dict[str, str]]:
        return extract_relations(text)

    def generate(self, prompt: str, max_new_tokens: int = 50) -> str:
        return generate_text(prompt, max_new_tokens=max_new_tokens)

    def translate(self, text: str, target_lang: str = "en") -> str:
        return translate_text(text, target_lang=target_lang)