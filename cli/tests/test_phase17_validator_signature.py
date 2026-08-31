"""Fase 17 Slice 3 — ModuleCLIValidator._check_signature reporta status honesto.

Antes da Ed25519SignatureProvider real (Slice 2), uma assinatura presente
sempre reportava UNSUPPORTED — "nenhum algoritmo disponível", o que já
não é verdade (Ed25519 existe e é verificável, só falta a public_key
aqui: este validador é síncrono/standalone, sem AsyncSession pro
Publisher Registry). Agora reporta NOT_CONFIGURED, que é o status
honesto e correto pra "não consigo verificar sem a chave".

Verificação criptográfica real (VALID/INVALID) só é possível na rota
assíncrona `GET /modules/{id}/trust` (ver test_phase17_signature_integration.py).

Run:  cd cli && python -m pytest tests/test_phase17_validator_signature.py -q
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core" / "backend"))


def _make_valid_module(tmp: Path, module_id: str = "test_mod") -> Path:
    """Cópia local do fixture de test_phase3.py — evitar import cruzado
    entre arquivos de teste do CLI, que não é confiável sob coleta de
    suíte completa (cli/tests não é um pacote, sem __init__.py)."""
    mod = tmp / module_id
    mod.mkdir(parents=True, exist_ok=True)
    (mod / "backend").mkdir()
    (mod / "frontend").mkdir()
    (mod / "assets").mkdir()
    (mod / "docs").mkdir()
    (mod / "tests").mkdir()

    (mod / "manifest.yaml").write_text(yaml.dump({
        "id": module_id,
        "name": "Test Module",
        "version": "1.0.0",
        "platform_min_version": "1.0.0",
        "platform_max_version": "2.0.0",
        "category": "Test",
        "vendor": "TechForge",
        "author": "Tester",
        "description": "A test module.",
        "entry_backend": "backend/main.py",
        "entry_frontend": "frontend/index.tsx",
        "icon": "shield-check",
        "order": 10,
        "color": "blue",
    }), encoding="utf-8")

    (mod / "docs" / "overview.md").write_text(
        "# Test Module\n\nThis is a test module used for automated testing.",
        encoding="utf-8",
    )
    (mod / "docs" / "examples").mkdir()
    (mod / "docs" / "examples" / "basic.md").write_text(
        "## Objetivo\n\nExemplo básico de uso.\n\n"
        "## Entradas\n\nNenhuma.\n\n"
        "## Saídas\n\n`dict` de status.\n\n"
        "## Exemplo\n\n```python\nresult = module.ping()\n```\n\n"
        "## Observações\n\nApenas para testes automatizados.",
        encoding="utf-8",
    )

    (mod / "backend" / "main.py").write_text(
        "from fastapi import APIRouter\n"
        "from techforge_sdk.contracts import ModuleContract\n"
        "router = APIRouter()\n"
        "moduleConfig = None\n"
    )
    (mod / "frontend" / "index.tsx").write_text(
        "export const moduleConfig = {}\n"
        "export default function Page() { return null }\n"
    )
    return mod


def _signature_check(report):
    return next(c for c in report.checks if c.name.startswith("Signature:"))


def test_module_without_signature_is_not_configured(tmp_path):
    from techforge_cli.validators.module_validator import ModuleCLIValidator

    mod = _make_valid_module(tmp_path)
    report = ModuleCLIValidator.validate(mod)

    check = _signature_check(report)
    assert "NOT_CONFIGURED" in check.message
    assert check.passed


def test_module_with_real_signature_but_no_public_key_is_not_configured(tmp_path):
    """Sem acesso ao Publisher Registry (sem DB neste validador), mesmo uma
    assinatura Ed25519 genuína não pode ser verificada aqui — e o status
    reportado precisa dizer isso honestamente, não fingir suporte
    indisponível (era o bug do NoOpSignatureProvider: UNSUPPORTED)."""
    from app.module_trust.signature import (
        Ed25519SignatureProvider,
        canonical_manifest_bytes,
        generate_ed25519_keypair,
    )
    from techforge_cli.validators.module_validator import ModuleCLIValidator

    mod = _make_valid_module(tmp_path)
    raw = yaml.safe_load((mod / "manifest.yaml").read_text(encoding="utf-8"))

    private_pem, _ = generate_ed25519_keypair()
    signature = Ed25519SignatureProvider().sign(canonical_manifest_bytes(raw), private_pem)
    raw["signature"] = base64.b64encode(signature).decode()
    (mod / "manifest.yaml").write_text(yaml.dump(raw), encoding="utf-8")

    report = ModuleCLIValidator.validate(mod)

    check = _signature_check(report)
    assert "NOT_CONFIGURED" in check.message
    assert check.passed  # nunca bloqueia — não é o mesmo que provar INVALID
