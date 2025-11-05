from typing import Dict, Any, List

from .transformer_wrapper import SafeHF


def analyze_document_sentiment(text: str) -> Dict[str, Any]:
    hf = SafeHF("sentiment-analysis")
    if hf.available:
        try:
            out = hf(text)
            # Normalizar salida
            if out and isinstance(out, list) and len(out) > 0:
                item = out[0]
                label = item.get("label", "neutral").lower()
                score = float(item.get("score", 0.0))
                mapped = "positive" if "pos" in label else "negative" if "neg" in label else "neutral"
                return {"label": mapped, "score": score}
        except Exception:
            pass
    # Fallback simple
    pos_words = {"bueno", "excelente", "genial", "feliz", "positivo", "great", "good", "happy", "awesome"}
    neg_words = {"malo", "terrible", "triste", "negativo", "awful", "bad", "sad", "worse"}
    tokens = [t.lower() for t in text.split()]
    pos = sum(1 for t in tokens if t in pos_words)
    neg = sum(1 for t in tokens if t in neg_words)
    denom = max(len(tokens), 1)
    score = (pos - neg) / denom
    label = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"
    return {"label": label, "score": round(score, 4)}


def analyze_sentence_sentiment(text: str) -> List[Dict[str, Any]]:
    # Partición ingenua por signos de puntuación
    sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    return [analyze_document_sentiment(s) for s in sentences]