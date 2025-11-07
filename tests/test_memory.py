import json
import pytest
from pathlib import Path

from src.lucy.lucy_ai import LucyAI


def _ensure_minimal_intents(config_manager):
    intents_dir = Path(config_manager.get_path('intents_dir'))
    intents_dir.mkdir(parents=True, exist_ok=True)
    minimal = {"intents": [{"tag": "saludo", "patterns": ["hola"], "responses": ["Hola!"]}]}
    for lang in ("es", "en"):
        (intents_dir / f"intents_{lang}.json").write_text(json.dumps(minimal), encoding="utf-8")

def test_memory_add_find_purge_status(config_manager):
    _ensure_minimal_intents(config_manager)
    ai = LucyAI(config_manager)

    # Status inicial
    status = json.loads(ai.process_message("!mem status"))
    assert isinstance(status, dict)
    assert status.get("enabled", True) is True

    # Add dos eventos
    resp1 = json.loads(ai.process_message("!mem add text=El pedido 123 fue entregado conv_id=soporte user_id=juan"))
    assert "event_id" in resp1
    resp2 = json.loads(ai.process_message("!mem add text=Consulta estado pedido 123 conv_id=soporte user_id=ana"))
    assert "event_id" in resp2

    # Find similar
    results = json.loads(ai.process_message("!mem find query=estado pedido 123 top_k=2"))
    assert isinstance(results, list)
    assert len(results) >= 1
    assert "contenido" in results[0]

    # Purge
    purged_info = json.loads(ai.process_message("!mem purge conv_id=soporte"))
    assert purged_info.get("purged", 0) >= 2

    # Status final
    status2 = json.loads(ai.process_message("!mem status"))
    assert status2.get("events", 0) == 0


def test_memory_fallback_without_embeddings_model(config_manager):
    _ensure_minimal_intents(config_manager)
    # Forzar embeddings.model a None via config manager
    cfg = config_manager.get_all()
    cfg['embeddings'] = {'model': None}
    config_manager.set('embeddings', cfg['embeddings'])

    ai = LucyAI(config_manager)
    _ = ai.process_message("!mem add text=Correo de contacto: test@example.com conv_id=ventas user_id=luis")
    res = json.loads(ai.process_message("!mem find query=contacto"))
    assert isinstance(res, list)
    # Verificar masking si habilitado
    status = json.loads(ai.process_message("!mem status"))
    # Si privacy.mask_emails true, el contenido no debe mostrar el correo literal
    if status.get('enabled'):
        # obtener el último resultado si existe
        if res:
            assert "[email]" in res[0]["contenido"] or "@" not in res[0]["contenido"]