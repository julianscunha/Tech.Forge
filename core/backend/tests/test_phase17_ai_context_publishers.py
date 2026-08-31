"""AIContextExporter consulta o Publisher Registry real.

Gap corrigido: a seção "Module Trust" do AI Context sempre resolvia trust_level com
`publisher=None`, mesmo quando o módulo declarava um publisher_id real —
nunca passava de UNVERIFIED. `export()` agora aceita um dict opcional
`{publisher_id: Publisher}` (pré-carregado pela rota assíncrona via
`PublisherService.get_all`, já que o exportador em si continua síncrono
— os ~15 call-sites de teste síncronos existentes continuam funcionando
sem o parâmetro, comportamento antigo preservado).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_ai_context_publishers.py -q
"""
from __future__ import annotations

import base64
from datetime import datetime

import pytest

from app.doc_engine import AIContextExporter, DocIndexer
from app.doc_engine.search import DocIndex
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import ModuleEntry, registry
from app.module_trust.integrity import write_integrity_manifest
from app.module_trust.signature import (
    Ed25519SignatureProvider,
    canonical_manifest_bytes,
    generate_ed25519_keypair,
)

pytestmark = pytest.mark.unit


class _FakePublisher:
    def __init__(self, public_key: str, trust_status: str):
        self.public_key = public_key
        self.trust_status = trust_status


def test_module_trust_section_uses_real_publisher_when_provided(tmp_path, monkeypatch):
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path / "installed")

    module_id = "ai_context_trust_test"
    publisher_id = "ai_context_publisher"
    private_pem, public_pem = generate_ed25519_keypair()

    mod_dir = tmp_path / "installed" / module_id
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
    write_integrity_manifest(mod_dir)

    manifest_raw = {"id": module_id, "publisher": {"id": publisher_id}}
    signature = Ed25519SignatureProvider().sign(canonical_manifest_bytes(manifest_raw), private_pem)
    manifest_raw["signature"] = base64.b64encode(signature).decode()

    registry.register(ModuleEntry(
        module_id=module_id, name=module_id, version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=ModuleStatus.INSTALLED, install_date=datetime.now(),
        manifest_raw=manifest_raw))

    indexer = DocIndexer(DocIndex(), docs_root=tmp_path / "developer-center",
                          installed_path=tmp_path / "installed")
    publishers = {publisher_id: _FakePublisher(public_pem.decode(), "TRUSTED")}

    try:
        markdown = AIContextExporter.export(indexer, publishers=publishers)
    finally:
        registry.deregister(module_id)

    assert f"### {module_id}" in markdown
    assert "**Trust Level:** TRUSTED" in markdown


def test_module_trust_section_without_publishers_param_is_unverified(tmp_path, monkeypatch):
    """Comportamento antigo preservado quando `publishers` não é passado
    (todos os call-sites de teste síncronos existentes, ex.: test_phase5.py)."""
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path / "installed")

    module_id = "ai_context_no_publishers_test"
    mod_dir = tmp_path / "installed" / module_id
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
    write_integrity_manifest(mod_dir)

    registry.register(ModuleEntry(
        module_id=module_id, name=module_id, version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=ModuleStatus.INSTALLED, install_date=datetime.now(),
        manifest_raw={"id": module_id, "publisher": {"id": "someone"}}))

    indexer = DocIndexer(DocIndex(), docs_root=tmp_path / "developer-center",
                          installed_path=tmp_path / "installed")

    try:
        markdown = AIContextExporter.export(indexer)
    finally:
        registry.deregister(module_id)

    assert f"### {module_id}" in markdown
    assert "**Trust Level:** UNVERIFIED" in markdown
