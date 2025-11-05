"""Pipelines avanzados de PLN (opcionalmente con Transformers)"""

from .transformer_wrapper import SafeHF
from .sentiment import analyze_document_sentiment, analyze_sentence_sentiment
from .generation import generate_text
from .translation import translate_text
from .ner import extract_entities
from .relation_extraction import extract_relations

__all__ = [
    "SafeHF",
    "analyze_document_sentiment",
    "analyze_sentence_sentiment",
    "generate_text",
    "translate_text",
    "extract_entities",
    "extract_relations",
]