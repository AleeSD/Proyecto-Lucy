import json
from pathlib import Path

from src.lucy.logging_system import ConversationLogger, PerformanceLogger, ErrorLogger


def test_conversation_logger_json_file(tmp_path):
    log_dir = tmp_path / "conv_logs"
    cl = ConversationLogger(log_dir=str(log_dir))

    cl.log_conversation(
        session_id="s-123",
        user_input="Hola Lucy",
        bot_response="Hola!",
        intent="greeting",
        confidence=0.99,
        language="es",
        response_time=0.12,
    )

    f = log_dir / "conversations.json"
    assert f.exists()
    content = f.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) >= 1
    # Cada línea debe ser un JSON válido con claves esperadas
    obj = json.loads(content[-1])
    for k in [
        "session_id",
        "user_input",
        "bot_response",
        "intent",
        "confidence",
        "language",
        "response_time",
        "timestamp",
    ]:
        assert k in obj


def test_performance_logger_json(tmp_path):
    log_dir = tmp_path / "perf_logs"
    pl = PerformanceLogger(log_dir=str(log_dir))

    pl.log_metric("response_time", 0.45, unit="seconds", tags={"feature": "test"})

    f = log_dir / "performance.log"
    assert f.exists()
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    obj = json.loads(lines[-1])
    assert obj.get("metric") == "response_time"
    assert "value" in obj
    assert obj.get("unit") == "seconds"
    assert obj.get("tags", {}).get("feature") == "test"


def test_error_logger_file(tmp_path):
    log_dir = tmp_path / "error_logs"
    el = ErrorLogger(log_dir=str(log_dir))

    try:
        raise ValueError("error de prueba")
    except Exception as e:
        el.log_error(e, context={"test": True})

    f = log_dir / "errors.log"
    assert f.exists()
    text = f.read_text(encoding="utf-8")
    assert "error de prueba" in text
    assert "Stack Trace" in text