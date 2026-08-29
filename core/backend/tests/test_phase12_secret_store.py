"""Fase 12 Slice 7 — Secret Store (spec §11/§28).

`context.secrets` — isolado por module_id (mesmo desenho estrutural do
Module Storage API, Slice 5). Backend real (`keyring`) nunca é exercitado
contra o cofre nativo do SO nos testes — sempre mockado/injetado, para não
depender de D-Bus/Secret Service/Credential Manager disponíveis em CI.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase12_secret_store.py -q
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import pytest

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.security.secret_store import (
    KeyringSecretStore,
    ModuleSecretStore,
    SecretStoreBackend,
    SecretStoreError,
    _known_secret_values,
)
from app.security.redaction import SecretRedactionFilter


class FakeBackend(SecretStoreBackend):
    def __init__(self):
        self.store: dict[tuple[str, str], str] = {}

    def get(self, module_id: str, key: str) -> Optional[str]:
        return self.store.get((module_id, key))

    def set(self, module_id: str, key: str, value: str) -> None:
        self.store[(module_id, key)] = value

    def delete(self, module_id: str, key: str) -> None:
        self.store.pop((module_id, key), None)


@pytest.fixture(autouse=True)
def _clean_known_secrets():
    _known_secret_values.clear()
    yield
    _known_secret_values.clear()


def test_get_returns_none_when_key_absent():
    secrets = ModuleSecretStore("mod_a", backend=FakeBackend())
    assert secrets.get("api_key") is None


def test_set_then_get_round_trips():
    secrets = ModuleSecretStore("mod_a", backend=FakeBackend())
    secrets.set("api_key", "sk-123")
    assert secrets.get("api_key") == "sk-123"


def test_modules_are_isolated_from_each_other():
    backend = FakeBackend()
    a = ModuleSecretStore("mod_a", backend=backend)
    b = ModuleSecretStore("mod_b", backend=backend)
    a.set("api_key", "sk-a")
    assert b.get("api_key") is None
    assert a.get("api_key") == "sk-a"


def test_delete_removes_secret():
    secrets = ModuleSecretStore("mod_a", backend=FakeBackend())
    secrets.set("api_key", "sk-123")
    secrets.delete("api_key")
    assert secrets.get("api_key") is None


def test_keyring_secret_store_delegates_to_keyring_module(monkeypatch):
    calls = []
    import keyring

    monkeypatch.setattr(keyring, "set_password", lambda service, key, value: calls.append((service, key, value)))
    monkeypatch.setattr(keyring, "get_password", lambda service, key: "sk-mocked")

    store = KeyringSecretStore()
    store.set("mod_a", "api_key", "sk-mocked")
    assert calls == [("techforge", "mod_a:api_key", "sk-mocked")]
    assert store.get("mod_a", "api_key") == "sk-mocked"


def test_keyring_secret_store_wraps_backend_errors(monkeypatch):
    import keyring

    def _raise(*a, **kw):
        raise RuntimeError("cofre indisponível")

    monkeypatch.setattr(keyring, "get_password", _raise)
    store = KeyringSecretStore()
    with pytest.raises(SecretStoreError):
        store.get("mod_a", "api_key")


def test_keyring_secret_store_set_registers_value_for_redaction(monkeypatch):
    import keyring

    monkeypatch.setattr(keyring, "set_password", lambda *a, **kw: None)
    store = KeyringSecretStore()
    store.set("mod_a", "api_key", "sk-secret-value")
    assert "sk-secret-value" in _known_secret_values


def test_redaction_filter_redacts_known_secret_value_in_log_message():
    _known_secret_values.add("sk-super-secret")
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="Conectando com token sk-super-secret", args=(), exc_info=None,
    )
    SecretRedactionFilter().filter(record)
    assert "sk-super-secret" not in record.getMessage()
    assert "***REDACTED***" in record.getMessage()


def test_redaction_filter_leaves_unrelated_messages_untouched():
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="Módulo instalado com sucesso", args=(), exc_info=None,
    )
    SecretRedactionFilter().filter(record)
    assert record.getMessage() == "Módulo instalado com sucesso"


def test_install_secret_redaction_filter_attaches_to_handler_not_logger():
    """Regressão: um Filter no Logger raiz NÃO se aplica a registros
    propagados de loggers filhos (techforge.module.*) — só um filtro no
    Handler pega. Usa um logger isolado (não o root real, que o pytest
    mexe entre testes) para o teste ser determinístico."""
    from app.main import _install_secret_redaction_filter

    fake_logger = logging.Logger("fase12_redaction_test_isolated")
    handler = logging.StreamHandler()
    fake_logger.addHandler(handler)

    _install_secret_redaction_filter(fake_logger)

    assert any(isinstance(f, SecretRedactionFilter) for f in handler.filters)


def test_module_execution_context_build_exposes_secrets_bound_to_module_id():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.module_runtime.context import ModuleExecutionContext
    from app.module_engine.registry import registry as module_registry

    with TestClient(app):
        ctx = ModuleExecutionContext.build("hello_world", module_registry)

    assert ctx is not None
    assert isinstance(ctx.secrets, ModuleSecretStore)
    assert ctx.secrets._module_id == "hello_world"
