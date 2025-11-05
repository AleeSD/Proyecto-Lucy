from typing import Dict, Any

from .transformer_wrapper import SafeHF


def generate_text(prompt: str, max_new_tokens: int = 50) -> str:
    hf = SafeHF("text-generation")
    if hf.available:
        try:
            out = hf(prompt, max_new_tokens=max_new_tokens)
            if out and isinstance(out, list) and len(out) > 0:
                return out[0].get("generated_text", "")
        except Exception:
            pass
    # Fallback: plantilla simple
    return f"{prompt} ..."