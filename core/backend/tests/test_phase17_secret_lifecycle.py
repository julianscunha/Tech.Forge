"""Fase 17 Slice 6 — Secret lifecycle explícito + redação (spec §22-26).

`ModuleSecretStore.rotate()` nomeado (antes só `set()` de novo, sem
distinção semântica) + eventos SECRET_CREATED/SECRET_ROTATED/SECRET_DELETED
via EventBus. Nenhum payload carrega o valor do segredo — só module_id
e key (metadado, não o segredo em si).

Padrão de redação de log ganha "authorization"/"Authorization: Bearer
xxx" explícito (spec §25 cita nominalmente) — corrige também um bug
real: o padrão anterior parava no primeiro espaço, então "Bearer xxx"
só teria "Bearer" redigido, deixando o token exposto.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_secret_lifecycle.py -q
"""
from __future__ import annotations

import logging

import pytest

from app.observability.events import event_bus
from app.security.secret_store import ModuleSecretStore, SecretStoreBackend

pytestmark = pytest.mark.unit


class _FakeBackend(SecretStoreBackend):
    """Backend em memória — evita tocar o keyring real do SO nos testes."""

    def __init__(self):
        self._values: dict[tuple[str, str], str] = {}

    def get(self, module_id, key):
        return self._values.get((module_id, key))

    def set(self, module_id, key, value):
        self._values[(module_id, key)] = value

    def delete(self, module_id, key):
        self._values.pop((module_id, key), None)


class _Catcher:
    def __init__(self):
        self.events = []

    def __call__(self, event):
        self.events.append(event)


def _capture():
    catcher = _Catcher()
    event_bus.subscribe(catcher)
    return catcher


def test_set_new_key_publishes_secret_created():
    store = ModuleSecretStore("mod_a", backend=_FakeBackend())
    catcher = _capture()
    try:
        store.set("api_key", "super-secret-value")
    finally:
        event_bus.unsubscribe(catcher)

    created = [e for e in catcher.events if e.type == "security.secret_created"]
    assert len(created) == 1
    assert created[0].payload == {"module_id": "mod_a", "key": "api_key"}
    assert "super-secret-value" not in str(created[0].payload)


def test_set_existing_key_does_not_publish_created_again():
    backend = _FakeBackend()
    store = ModuleSecretStore("mod_a", backend=backend)
    store.set("api_key", "v1")

    catcher = _capture()
    try:
        store.set("api_key", "v2")  # overwrite via set(), nao rotate()
    finally:
        event_bus.unsubscribe(catcher)

    assert not [e for e in catcher.events if e.type == "security.secret_created"]


def test_rotate_existing_key_publishes_secret_rotated():
    backend = _FakeBackend()
    store = ModuleSecretStore("mod_a", backend=backend)
    store.set("api_key", "old-value")

    catcher = _capture()
    try:
        store.rotate("api_key", "new-value")
    finally:
        event_bus.unsubscribe(catcher)

    assert store.get("api_key") == "new-value"
    rotated = [e for e in catcher.events if e.type == "security.secret_rotated"]
    assert len(rotated) == 1
    assert rotated[0].payload == {"module_id": "mod_a", "key": "api_key"}
    assert "old-value" not in str(rotated[0].payload)
    assert "new-value" not in str(rotated[0].payload)


def test_rotate_nonexistent_key_raises():
    from app.security.secret_store import SecretStoreError

    store = ModuleSecretStore("mod_a", backend=_FakeBackend())
    with pytest.raises(SecretStoreError):
        store.rotate("never_set", "value")


def test_delete_existing_key_publishes_secret_deleted():
    backend = _FakeBackend()
    store = ModuleSecretStore("mod_a", backend=backend)
    store.set("api_key", "v1")

    catcher = _capture()
    try:
        store.delete("api_key")
    finally:
        event_bus.unsubscribe(catcher)

    deleted = [e for e in catcher.events if e.type == "security.secret_deleted"]
    assert len(deleted) == 1
    assert deleted[0].payload == {"module_id": "mod_a", "key": "api_key"}


def test_delete_nonexistent_key_does_not_publish_deleted():
    store = ModuleSecretStore("mod_a", backend=_FakeBackend())
    catcher = _capture()
    try:
        store.delete("never_set")  # idempotente — sem erro, sem evento
    finally:
        event_bus.unsubscribe(catcher)

    assert not [e for e in catcher.events if e.type == "security.secret_deleted"]


# ── Redação: authorization header (spec §25) ────────────────────────────────

def _make_record(msg: str) -> logging.LogRecord:
    return logging.LogRecord(name="test", level=logging.INFO, pathname=__file__,
                             lineno=1, msg=msg, args=(), exc_info=None)


class TestAuthorizationRedaction:

    def test_redacts_authorization_header_with_bearer_token(self):
        from app.security.redaction import SecretRedactionFilter

        record = _make_record("sending request with Authorization: Bearer sk-abc123xyz")
        SecretRedactionFilter().filter(record)
        message = record.getMessage()

        assert "sk-abc123xyz" not in message
        assert "Bearer" not in message  # o valor inteiro do header e redigido, nao so um pedaco
        assert "***REDACTED***" in message

    def test_redacts_authorization_key_value_style(self):
        from app.security.redaction import SecretRedactionFilter

        record = _make_record('headers: {"authorization": "Bearer xyz"}')
        SecretRedactionFilter().filter(record)
        message = record.getMessage()

        assert "xyz" not in message
        assert "***REDACTED***" in message
