from src.lucy.config_manager import ConfigManager
from src.lucy.nlp import AdvancedNLPManager


def test_nlp_sentiment_positive(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text("{}", encoding="utf-8")
    cm = ConfigManager(str(cfg_path), auto_reload=False)
    cm.set("advanced_nlp", {"enabled": True, "keywords": {"top_n": 3}})
    nlp = AdvancedNLPManager(cm)
    res = nlp.analyze("Me siento muy feliz y genial hoy")
    assert res["sentiment"]["label"] == "positive"


def test_nlp_sentiment_negative(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text("{}", encoding="utf-8")
    cm = ConfigManager(str(cfg_path), auto_reload=False)
    cm.set("advanced_nlp", {"enabled": True})
    nlp = AdvancedNLPManager(cm)
    res = nlp.analyze("Esto es malo y terrible")
    assert res["sentiment"]["label"] == "negative"


def test_nlp_entities(tmp_path):
    cm = ConfigManager(str(tmp_path / "cfg.json"), auto_reload=False)
    cm.save(str(tmp_path / "cfg.json"))
    cm.set("advanced_nlp", {"enabled": True})
    nlp = AdvancedNLPManager(cm)
    text = "Contáctame en test@example.com el 2025-11-05, total 123.5"
    res = nlp.analyze(text)
    assert "test@example.com" in res["entities"]["emails"]
    assert "2025-11-05" in res["entities"]["dates"]
    assert any(n in res["entities"]["numbers"] for n in ["123.5", "123"])