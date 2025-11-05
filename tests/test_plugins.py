from pathlib import Path
import json

from src.lucy.config_manager import ConfigManager
from src.lucy.plugins.manager import PluginManager, PluginResult


def _write_temp_plugin(tmp_path: Path):
    code = (
        "from src.lucy.plugins.manager import PluginInterface, PluginResult\n"
        "class TempPlugin(PluginInterface):\n"
        "    name='temp'\n"
        "    version='0.0.1'\n"
        "    def on_message(self, message, context, engine):\n"
        "        if message.strip().startswith('!temp '):\n"
        "            return PluginResult(handled=True, response='TEMP:' + message[6:])\n"
        "        return PluginResult(handled=False)\n"
    )
    f = tmp_path / "temp_plugin.py"
    f.write_text(code, encoding="utf-8")
    return f


def test_plugin_manager_discovery_and_handle_message(tmp_path):
    # Crear plugin temporal
    _write_temp_plugin(tmp_path)

    # Config con plugins habilitados
    cfg = {
        "app": {"name": "Test", "version": "1.0.0"},
        "model": {"default_language": "es", "confidence_threshold": 0.3},
        "paths": {
            "data_dir": "data",
            "models_dir": "data/models",
            "intents_dir": "data/intents",
            "logs_dir": "logs"
        },
        "plugins": {"enabled": True, "dirs": [str(tmp_path)]},
    }
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    cm = ConfigManager(config_path=str(cfg_path), auto_reload=False)
    pm = PluginManager(cm)
    pm.start(engine=None)

    # Mensaje manejado por plugin
    res: PluginResult = pm.handle_message("!temp hola", context=[])
    assert res.handled is True
    assert res.response == "TEMP:hola"

    # Mensaje no manejado
    res2: PluginResult = pm.handle_message("hola", context=[])
    assert res2.handled is False