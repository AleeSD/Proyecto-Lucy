import json
import os
import pytest
from pathlib import Path

from src.lucy.database import ConversationDB
from src.lucy.config_manager import ConfigManager

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_conversations.db")

@pytest.fixture
def conversation_db(temp_db_path):
    db = ConversationDB(temp_db_path)
    yield db
    # No persistent connection; logger handles close message

@pytest.fixture
def test_config_path(tmp_path):
    cfg = {
        "app": {"name": "Test Lucy", "version": "1.0.0"},
        "model": {"default_language": "es", "confidence_threshold": 0.3},
        "paths": {
            "data_dir": "data",
            "models_dir": "data/models",
            "intents_dir": "data/intents",
            "logs_dir": "logs"
        },
        "logging": {"level": "INFO", "file_enabled": True}
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return str(p)

@pytest.fixture
def config_manager(test_config_path):
    # Desactivar auto_reload para evitar hilos en pruebas
    return ConfigManager(config_path=test_config_path, auto_reload=False)