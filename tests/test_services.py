import pytest

from src.lucy.services import ServiceManager


def test_service_manager_loads_dummy(config_manager):
    # Activar servicios externos con configuración de dummy
    config_manager.set("external_services", {
        "enabled": True,
        "services": {
            "dummy": {"prefix": "ECHO: "}
        }
    })

    sm = ServiceManager(config_manager)
    res = sm.execute("dummy", "echo", {"text": "hola"})
    assert res == "ECHO: hola"


def test_service_manager_sum_operation(config_manager):
    config_manager.set("external_services", {"enabled": True})
    sm = ServiceManager(config_manager)
    res = sm.execute("dummy", "sum", {"a": 2, "b": 3})
    assert res == 5


def test_service_manager_disabled(config_manager):
    config_manager.set("external_services", {"enabled": False})
    sm = ServiceManager(config_manager)
    res = sm.execute("dummy", "echo", {"text": "hola"})
    assert res is None