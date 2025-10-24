import json
from pathlib import Path

import pytest

from src.lucy.config_manager import ConfigManager


def test_load_get_set_save_reload(config_manager, test_config_path):
    # get
    assert config_manager.get("app.name") == "Test Lucy"
    assert config_manager.get("model.confidence_threshold") == 0.3
    # get default cuando no existe
    assert config_manager.get("features.experimental", False) is False

    # set y save
    config_manager.set("features.new_pipeline", True)
    assert config_manager.get("features.new_pipeline") is True

    save_path = Path(test_config_path).parent / "saved_config.json"
    config_manager.save(str(save_path))
    assert save_path.exists()

    # reload desde archivo guardado
    cm2 = ConfigManager(config_path=str(save_path), auto_reload=False)
    assert cm2.get("features.new_pipeline") is True


def test_observer_and_reload(tmp_path):
    # crear archivo config
    cfg_path = tmp_path / "cfg.json"
    cfg = {
        "app": {"name": "Lucy", "version": "1.0.0"},
        "model": {"default_language": "es", "confidence_threshold": 0.5},
        "paths": {
            "data_dir": "data",
            "models_dir": "data/models",
            "intents_dir": "data/intents",
            "logs_dir": "logs"
        },
        "logging": {"level": "INFO", "file_enabled": True}
    }
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    cm = ConfigManager(config_path=str(cfg_path), auto_reload=False)

    calls = []
    def observer(new_cfg):
        calls.append(new_cfg)

    cm.register_observer(lambda _: None)  # dummy
    cm.register_observer(observer)

    # modificar archivo
    cfg["model"]["confidence_threshold"] = 0.7
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    cm.reload_config()
    assert cm.get("model.confidence_threshold") == 0.7
    assert len(calls) >= 1
    assert isinstance(calls[-1], dict)


def test_get_path_and_errors(config_manager):
    p = config_manager.get_path("logs_dir")
    # debe ser posix (con /), incluso en Windows
    assert "/" in p

    # Forzar error cuando la ruta no está configurada
    config_manager.set("paths.logs_dir", "")
    with pytest.raises(ValueError):
        config_manager.get_path("logs_dir")


def test_is_feature_enabled(config_manager):
    config_manager.set("features.metrics", True)
    assert config_manager.is_feature_enabled("metrics") is True
    assert config_manager.is_feature_enabled("nonexistent") is False