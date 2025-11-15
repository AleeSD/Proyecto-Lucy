from .transformer_wrapper import SafeHF


_DICT_ES_EN = {
    "hola": "hello",
    "mundo": "world",
    "gracias": "thanks",
    "bien": "well",
}
_DICT_EN_ES = {v: k for k, v in _DICT_ES_EN.items()}


def translate_text(text: str, target_lang: str = "en") -> str:
    target_lang = (target_lang or "en").lower()
    # Intentar MarianMT/MBART por pipeline genérico de traducción
    task = "translation" if target_lang in ("en", "es") else "translation"
    hf = SafeHF(task)
    if hf.available:
        try:
            out = hf(text)
            if out and isinstance(out, list) and len(out) > 0:
                # Algunas pipelines devuelven 'translation_text'
                return out[0].get("translation_text", out[0].get("generated_text", ""))
        except Exception:
            pass
    # Fallback diccionario mínimo
    tokens = text.split()
    if target_lang == "en":
        return " ".join(_DICT_ES_EN.get(t.lower(), t) for t in tokens)
    if target_lang == "es":
        return " ".join(_DICT_EN_ES.get(t.lower(), t) for t in tokens)
    return text