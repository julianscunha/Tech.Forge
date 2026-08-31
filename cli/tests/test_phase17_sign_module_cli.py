"""Fase 17 Slice 2 — CLI: trust generate-keypair, sign-module.

Operações locais de criptografia — não dependem da plataforma rodando
(diferente de verify-module/publishers, que consomem a API do Core).

Run:  cd cli && python -m pytest tests/test_phase17_sign_module_cli.py -q
"""
from __future__ import annotations

import base64

import pytest
import yaml
from click.testing import CliRunner

pytestmark = pytest.mark.integration


def test_trust_cmd_has_generate_keypair_subcommand():
    from techforge_cli.commands.module_trust import trust_cmd
    assert "generate-keypair" in trust_cmd.commands


def test_sign_module_cmd_registered():
    from techforge_cli.commands.module_trust import sign_module_cmd
    assert sign_module_cmd.name == "sign-module"


def test_all_commands_registered_in_main_cli():
    from techforge_cli.main import cli
    assert "trust" in cli.commands
    assert "sign-module" in cli.commands


def test_generate_keypair_writes_pem_files(tmp_path):
    from techforge_cli.commands.module_trust import trust_cmd

    runner = CliRunner()
    result = runner.invoke(trust_cmd, ["generate-keypair", "--output-dir", str(tmp_path), "--name", "test-signer"])

    assert result.exit_code == 0, result.output
    private_pem = (tmp_path / "test-signer_private.pem").read_bytes()
    public_pem = (tmp_path / "test-signer_public.pem").read_bytes()
    assert private_pem.startswith(b"-----BEGIN PRIVATE KEY-----")
    assert public_pem.startswith(b"-----BEGIN PUBLIC KEY-----")


def test_sign_module_writes_signature_into_manifest(tmp_path):
    from techforge_cli.commands.module_trust import sign_module_cmd, trust_cmd

    runner = CliRunner()
    keys_dir = tmp_path / "keys"
    keys_dir.mkdir()
    keygen = runner.invoke(trust_cmd, ["generate-keypair", "--output-dir", str(keys_dir), "--name", "dev"])
    assert keygen.exit_code == 0, keygen.output

    module_dir = tmp_path / "my_module"
    module_dir.mkdir()
    manifest = {"id": "my_module", "version": "1.0.0", "name": "My Module"}
    manifest_path = module_dir / "manifest.yaml"
    manifest_path.write_text(yaml.dump(manifest), encoding="utf-8")

    result = runner.invoke(sign_module_cmd, [
        str(module_dir), "--key", str(keys_dir / "dev_private.pem"),
    ])
    assert result.exit_code == 0, result.output

    signed_manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert signed_manifest["signature"]
    assert signed_manifest["id"] == "my_module"

    # A assinatura de fato verifica contra a chave pública correspondente.
    from app.module_trust.signature import (
        Ed25519SignatureProvider,
        SignatureStatus,
        canonical_manifest_bytes,
    )
    unsigned = {k: v for k, v in signed_manifest.items() if k != "signature"}
    public_pem = (keys_dir / "dev_public.pem").read_text(encoding="utf-8")
    status = Ed25519SignatureProvider().verify(
        canonical_manifest_bytes(unsigned),
        base64.b64decode(signed_manifest["signature"]),
        public_pem,
    )
    assert status == SignatureStatus.VALID


def test_sign_module_fails_without_manifest(tmp_path):
    from techforge_cli.commands.module_trust import sign_module_cmd, trust_cmd

    runner = CliRunner()
    keys_dir = tmp_path / "keys"
    keys_dir.mkdir()
    runner.invoke(trust_cmd, ["generate-keypair", "--output-dir", str(keys_dir), "--name", "dev"])

    empty_dir = tmp_path / "no_manifest_here"
    empty_dir.mkdir()

    result = runner.invoke(sign_module_cmd, [
        str(empty_dir), "--key", str(keys_dir / "dev_private.pem"),
    ])
    assert result.exit_code != 0
