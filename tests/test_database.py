import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.lucy.database import ConversationDB


def test_database_creation(temp_db_path):
    db = ConversationDB(temp_db_path)
    assert Path(temp_db_path).exists(), "El archivo de base de datos debe existir"

    stats = db.get_database_stats()
    assert "database_size_bytes" in stats
    assert isinstance(stats["database_size_bytes"], int)


def test_save_and_get_conversation_history(conversation_db):
    session_id = "session-1"
    conversation_db.save_conversation(
        session_id=session_id,
        user_input="Hola",
        bot_response="Hola! ¿En qué puedo ayudarte?",
        intent="greeting",
        confidence=0.95,
        language="es",
        context={"channel": "test"}
    )
    conversation_db.save_conversation(
        session_id=session_id,
        user_input="¿Qué hora es?",
        bot_response="Son las 10:00",
        intent="ask_time",
        confidence=0.75,
        language="es",
        context={"channel": "test"}
    )

    history = conversation_db.get_conversation_history(session_id=session_id)
    assert len(history) == 2
    # Orden esperado: más reciente primero
    assert history[0]["intent"] == "ask_time"
    assert history[1]["intent"] == "greeting"


def test_metrics_summary_and_cleanup(conversation_db):
    # Insertar varias conversaciones
    for i in range(5):
        conversation_db.save_conversation(
            session_id=f"s{i}",
            user_input=f"msg {i}",
            bot_response=f"resp {i}",
            intent="test",
            confidence=0.5,
            language="es",
            context={"idx": i}
        )

    summary = conversation_db.get_metrics_summary(hours=7)
    assert "total_conversations" in summary
    assert summary["total_conversations"] >= 5

    # Con days_to_keep=0, todo lo anterior es menor que 'ahora' y se elimina
    # Forzar que las conversaciones sean antiguas para probar limpieza
    with conversation_db._get_connection() as conn:
        conn.execute("UPDATE conversations SET timestamp = '2000-01-01 00:00:00'")
        conn.commit()

    cleanup = conversation_db.cleanup_old_data(days_to_keep=365)
    assert cleanup["conversations_deleted"] >= 5

    # Confirmar que historia está vacía para una sesión insertada antes
    h = conversation_db.get_conversation_history(session_id="s0")
    assert len(h) == 0