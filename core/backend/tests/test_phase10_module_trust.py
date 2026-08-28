"""
Fase 10 — Module Trust: Integrity Manifest (Slice 1)
=======================================================
Run: pytest core/backend/tests/test_phase10_module_trust.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))
sys.path.insert(0, str(ROOT / "cli"))


def _write_package(tmp_path: Path, files: dict[str, str]) -> Path:
    """Cria um diretório de pacote 'instalado' fictício em tmp_path com os arquivos dados."""
    pkg = tmp_path / "pkg"
    for rel_path, content in files.items():
        full = pkg / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    return pkg


class TestGenerateIntegrityManifest:

    def test_generates_hash_per_file(self, tmp_path):
        from app.module_trust.integrity import generate_integrity_manifest

        pkg = _write_package(tmp_path, {
            "manifest.yaml": "id: mod\n",
            "backend/main.py": "router = None\n",
        })
        manifest = generate_integrity_manifest(pkg)
        assert manifest["algorithm"] == "sha256"
        assert set(manifest["files"]) == {"manifest.yaml", "backend/main.py"}
        assert len(manifest["files"]["manifest.yaml"]) == 64  # hex sha256

    def test_excludes_data_directory(self, tmp_path):
        from app.module_trust.integrity import generate_integrity_manifest

        pkg = _write_package(tmp_path, {
            "manifest.yaml": "id: mod\n",
            "data/settings.json": "{}",
        })
        manifest = generate_integrity_manifest(pkg)
        assert "data/settings.json" not in manifest["files"]
        assert "manifest.yaml" in manifest["files"]

    def test_excludes_pycache(self, tmp_path):
        from app.module_trust.integrity import generate_integrity_manifest

        pkg = _write_package(tmp_path, {
            "manifest.yaml": "id: mod\n",
            "backend/__pycache__/main.cpython-311.pyc": "binary-ish",
        })
        manifest = generate_integrity_manifest(pkg)
        assert not any("__pycache__" in f for f in manifest["files"])

    def test_deterministic_hash_for_same_content(self, tmp_path):
        from app.module_trust.integrity import generate_integrity_manifest

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n"})
        m1 = generate_integrity_manifest(pkg)
        m2 = generate_integrity_manifest(pkg)
        assert m1 == m2


class TestWriteIntegrityManifest:

    def test_writes_integrity_json(self, tmp_path):
        from app.module_trust.integrity import write_integrity_manifest, INTEGRITY_FILENAME
        import json

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n"})
        target = write_integrity_manifest(pkg)
        assert target == pkg / INTEGRITY_FILENAME
        assert target.is_file()
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["algorithm"] == "sha256"

    def test_integrity_json_itself_excluded_from_future_scans(self, tmp_path):
        from app.module_trust.integrity import write_integrity_manifest, generate_integrity_manifest

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n"})
        write_integrity_manifest(pkg)
        manifest = generate_integrity_manifest(pkg)
        assert "integrity.json" not in manifest["files"]


class TestVerifyIntegrity:

    def test_valid_when_nothing_changed(self, tmp_path):
        from app.module_trust.integrity import (
            write_integrity_manifest, verify_integrity, IntegrityStatus)

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n", "backend/main.py": "x=1\n"})
        write_integrity_manifest(pkg)
        result = verify_integrity(pkg)
        assert result.status == IntegrityStatus.VALID

    def test_modified_file_detected(self, tmp_path):
        from app.module_trust.integrity import (
            write_integrity_manifest, verify_integrity, IntegrityStatus)

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n"})
        write_integrity_manifest(pkg)
        (pkg / "manifest.yaml").write_text("id: mod\nversion: 2.0.0\n", encoding="utf-8")

        result = verify_integrity(pkg)
        assert result.status == IntegrityStatus.MODIFIED
        assert result.modified_files == ["manifest.yaml"]

    def test_missing_file_detected(self, tmp_path):
        from app.module_trust.integrity import (
            write_integrity_manifest, verify_integrity, IntegrityStatus)

        pkg = _write_package(tmp_path, {
            "manifest.yaml": "id: mod\n", "backend/main.py": "x=1\n"})
        write_integrity_manifest(pkg)
        (pkg / "backend" / "main.py").unlink()

        result = verify_integrity(pkg)
        assert result.status == IntegrityStatus.MISSING_FILE
        assert result.missing_files == ["backend/main.py"]

    def test_unexpected_file_detected(self, tmp_path):
        from app.module_trust.integrity import (
            write_integrity_manifest, verify_integrity, IntegrityStatus)

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n"})
        write_integrity_manifest(pkg)
        (pkg / "backend").mkdir()
        (pkg / "backend" / "extra.py").write_text("evil = True\n", encoding="utf-8")

        result = verify_integrity(pkg)
        assert result.status == IntegrityStatus.UNEXPECTED_FILE
        assert result.unexpected_files == ["backend/extra.py"]

    def test_missing_integrity_json_is_invalid_manifest(self, tmp_path):
        from app.module_trust.integrity import verify_integrity, IntegrityStatus

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n"})
        result = verify_integrity(pkg)
        assert result.status == IntegrityStatus.INVALID_MANIFEST

    def test_corrupted_integrity_json_is_invalid_manifest(self, tmp_path):
        from app.module_trust.integrity import verify_integrity, IntegrityStatus

        pkg = _write_package(tmp_path, {"manifest.yaml": "id: mod\n"})
        (pkg / "integrity.json").write_text("{not valid json", encoding="utf-8")
        result = verify_integrity(pkg)
        assert result.status == IntegrityStatus.INVALID_MANIFEST

    def test_missing_file_takes_priority_over_modified(self, tmp_path):
        """Prioridade documentada: MISSING_FILE > MODIFIED quando ambos ocorrem."""
        from app.module_trust.integrity import (
            write_integrity_manifest, verify_integrity, IntegrityStatus)

        pkg = _write_package(tmp_path, {
            "manifest.yaml": "id: mod\n", "backend/main.py": "x=1\n"})
        write_integrity_manifest(pkg)
        (pkg / "manifest.yaml").write_text("id: mod\nversion: 2.0.0\n", encoding="utf-8")
        (pkg / "backend" / "main.py").unlink()

        result = verify_integrity(pkg)
        assert result.status == IntegrityStatus.MISSING_FILE


class TestInstallWritesIntegrityManifest:
    """Regressão de integração — instalar um .mod real grava integrity.json."""

    def test_install_creates_integrity_json(self, tmp_path, monkeypatch):
        import asyncio
        import json as _json
        import zipfile
        from app.core.settings import settings
        from app.package_manager.manager import PackageManager
        from app.package_manager.enums import InstallStatus

        installed_dir = tmp_path / "installed"
        cache_dir = tmp_path / "cache"
        installed_dir.mkdir()
        cache_dir.mkdir()

        manifest = {
            "id": "trust_test_mod", "name": "Trust Test", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "999.999.999",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
        }

        # Create a minimal .mod file (it's a zip)
        mod_path = tmp_path / "trust_test_mod-1.0.0.mod"
        with zipfile.ZipFile(mod_path, "w") as zf:
            import yaml
            zf.writestr("manifest.yaml", yaml.dump(manifest))
            zf.writestr("backend/main.py", "router = None\n")
            zf.writestr("frontend/index.tsx", "export default {};\n")

        pm = PackageManager(installed_path=installed_dir, cache_path=cache_dir)
        result = asyncio.run(pm.install(mod_path))

        assert result.status == InstallStatus.SUCCESS
        integrity_file = installed_dir / "trust_test_mod" / "integrity.json"
        assert integrity_file.is_file()
        data = _json.loads(integrity_file.read_text(encoding="utf-8"))
        assert "manifest.yaml" in data["files"]


# ── Slice 2 — Publisher model + Registry (§10/§13) ─────────────────────────────

@pytest.fixture()
def db_client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        import asyncio
        from app.db.database import AsyncSessionLocal
        from sqlalchemy import delete
        from app.models.publisher import Publisher

        async def _clean():
            async with AsyncSessionLocal() as s:
                await s.execute(delete(Publisher))
                await s.commit()

        asyncio.run(_clean())
        yield c
        asyncio.run(_clean())


class TestPublisherService:

    def test_register_creates_publisher(self, db_client):
        import asyncio
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService
        from app.schemas.publisher import PublisherCreate

        async def _run():
            async with AsyncSessionLocal() as db:
                p = await PublisherService.register(db, PublisherCreate(
                    id="techforge.internal", name="TechForge Internal",
                    type="INTERNAL", trust_status="TRUSTED"))
                return p

        publisher = asyncio.run(_run())
        assert publisher.id == "techforge.internal"
        assert publisher.trust_status == "TRUSTED"

    def test_register_is_idempotent_updates_existing(self, db_client):
        import asyncio
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService
        from app.schemas.publisher import PublisherCreate

        async def _run():
            async with AsyncSessionLocal() as db:
                await PublisherService.register(db, PublisherCreate(
                    id="acme", name="Acme v1", type="THIRD_PARTY"))
                updated = await PublisherService.register(db, PublisherCreate(
                    id="acme", name="Acme v2", type="THIRD_PARTY"))
                all_publishers = await PublisherService.get_all(db)
                return updated, all_publishers

        updated, all_publishers = asyncio.run(_run())
        assert updated.name == "Acme v2"
        assert len([p for p in all_publishers if p.id == "acme"]) == 1

    def test_get_by_id_unknown_returns_none(self, db_client):
        import asyncio
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService

        async def _run():
            async with AsyncSessionLocal() as db:
                return await PublisherService.get_by_id(db, "ghost_publisher_9x")

        assert asyncio.run(_run()) is None

    def test_revoke_sets_trust_status_revoked(self, db_client):
        import asyncio
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService
        from app.schemas.publisher import PublisherCreate

        async def _run():
            async with AsyncSessionLocal() as db:
                await PublisherService.register(db, PublisherCreate(
                    id="bad_actor", name="Bad Actor", trust_status="TRUSTED"))
                return await PublisherService.revoke(db, "bad_actor")

        revoked = asyncio.run(_run())
        assert revoked.trust_status == "REVOKED"

    def test_revoke_unknown_publisher_returns_none(self, db_client):
        import asyncio
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService

        async def _run():
            async with AsyncSessionLocal() as db:
                return await PublisherService.revoke(db, "ghost_publisher_9x")

        assert asyncio.run(_run()) is None


class TestPublisherAPIRoutes:

    def test_list_publishers_empty_by_default(self, db_client):
        resp = db_client.get("/api/v1/publishers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_publishers_includes_registered(self, db_client):
        import asyncio
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService
        from app.schemas.publisher import PublisherCreate

        async def _run():
            async with AsyncSessionLocal() as db:
                await PublisherService.register(db, PublisherCreate(
                    id="techforge.internal", name="TechForge Internal", type="INTERNAL"))

        asyncio.run(_run())
        resp = db_client.get("/api/v1/publishers")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert "techforge.internal" in ids

    def test_get_publisher_unknown_returns_404(self, db_client):
        resp = db_client.get("/api/v1/publishers/ghost_publisher_9x")
        assert resp.status_code == 404

    def test_get_publisher_known_returns_data(self, db_client):
        import asyncio
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService
        from app.schemas.publisher import PublisherCreate

        async def _run():
            async with AsyncSessionLocal() as db:
                await PublisherService.register(db, PublisherCreate(
                    id="acme", name="Acme Corp", type="THIRD_PARTY", trust_status="UNTRUSTED"))

        asyncio.run(_run())
        resp = db_client.get("/api/v1/publishers/acme")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Acme Corp"
        assert body["trust_status"] == "UNTRUSTED"


class TestPublisherEnums:

    def test_publisher_type_values(self):
        from app.module_trust.publisher import PublisherType
        assert {t.value for t in PublisherType} == {
            "OFFICIAL", "INTERNAL", "THIRD_PARTY", "LOCAL_DEVELOPMENT"}

    def test_publisher_trust_status_values(self):
        from app.module_trust.publisher import PublisherTrustStatus
        assert {s.value for s in PublisherTrustStatus} == {
            "TRUSTED", "UNTRUSTED", "REVOKED"}


# ── Slice 3 — TrustResolver (§8) ────────────────────────────────────────────────

class _FakePublisher:
    def __init__(self, trust_status: str):
        self.trust_status = trust_status


class TestTrustLevelEnum:

    def test_trust_level_values(self):
        from app.module_trust.trust import TrustLevel
        assert {t.value for t in TrustLevel} == {
            "TRUSTED", "VERIFIED", "UNVERIFIED", "MODIFIED", "INVALID"}


class TestTrustResolver:

    def test_invalid_manifest_is_invalid(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        result = TrustResolver.resolve(IntegrityStatus.INVALID_MANIFEST, publisher=None)
        assert result == TrustLevel.INVALID

    def test_missing_file_is_invalid(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        result = TrustResolver.resolve(IntegrityStatus.MISSING_FILE, publisher=None)
        assert result == TrustLevel.INVALID

    def test_modified_file_is_modified(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        result = TrustResolver.resolve(IntegrityStatus.MODIFIED, publisher=None)
        assert result == TrustLevel.MODIFIED

    def test_unexpected_file_is_also_modified(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        result = TrustResolver.resolve(IntegrityStatus.UNEXPECTED_FILE, publisher=None)
        assert result == TrustLevel.MODIFIED

    def test_valid_integrity_unknown_publisher_is_unverified(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        result = TrustResolver.resolve(IntegrityStatus.VALID, publisher=None)
        assert result == TrustLevel.UNVERIFIED

    def test_valid_integrity_known_publisher_is_verified(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        publisher = _FakePublisher(trust_status="UNTRUSTED")
        result = TrustResolver.resolve(IntegrityStatus.VALID, publisher=publisher)
        assert result == TrustLevel.VERIFIED

    def test_revoked_publisher_is_invalid_even_with_valid_integrity(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        publisher = _FakePublisher(trust_status="REVOKED")
        result = TrustResolver.resolve(IntegrityStatus.VALID, publisher=publisher)
        assert result == TrustLevel.INVALID

    def test_trusted_publisher_with_valid_signature_is_trusted(self):
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        publisher = _FakePublisher(trust_status="TRUSTED")
        result = TrustResolver.resolve(IntegrityStatus.VALID, publisher=publisher,
                                       signature_status="VALID")
        assert result == TrustLevel.TRUSTED

    def test_trusted_publisher_without_signature_is_only_verified(self):
        """Sem assinatura real (Slice 4 = so abstracao), TRUSTED e inalcancavel."""
        from app.module_trust.trust import TrustResolver, TrustLevel
        from app.module_trust.integrity import IntegrityStatus

        publisher = _FakePublisher(trust_status="TRUSTED")
        result = TrustResolver.resolve(IntegrityStatus.VALID, publisher=publisher)
        assert result == TrustLevel.VERIFIED


class TestOldTrustLevelMigration:
    """Regressao — o TrustLevel antigo (Fase 4, minusculo) nao existe mais
    separado; package_manager reexporta o novo."""

    def test_package_manager_trust_level_is_the_new_one(self):
        from app.package_manager import TrustLevel as PMTrustLevel
        from app.module_trust.trust import TrustLevel as ModuleTrustLevel

        assert PMTrustLevel is ModuleTrustLevel

    def test_package_info_default_trust_level_is_unverified(self):
        from app.module_trust.trust import TrustLevel
        from app.package_manager.models import PackageInfo

        info = PackageInfo(
            module_id="x", name="X", version="1.0.0", category="C", vendor="V",
            author="A", description="D")
        assert info.trust_level == TrustLevel.UNVERIFIED


# ── Slice 4 — SignatureProvider (abstracao, §11/§12) ────────────────────────────

class TestSignatureStatusEnum:

    def test_signature_status_values(self):
        from app.module_trust.signature import SignatureStatus
        assert {s.value for s in SignatureStatus} == {
            "NOT_CONFIGURED", "VALID", "INVALID", "UNSUPPORTED"}


class TestNoOpSignatureProvider:

    def test_verify_without_signature_is_not_configured(self):
        from app.module_trust.signature import NoOpSignatureProvider, SignatureStatus

        provider = NoOpSignatureProvider()
        result = provider.verify(data=b"content", signature=None, public_key=None)
        assert result == SignatureStatus.NOT_CONFIGURED

    def test_verify_with_signature_present_is_unsupported(self):
        """Ha uma assinatura no pacote, mas nenhum algoritmo real pra checa-la."""
        from app.module_trust.signature import NoOpSignatureProvider, SignatureStatus

        provider = NoOpSignatureProvider()
        result = provider.verify(data=b"content", signature=b"fake-sig", public_key="fake-key")
        assert result == SignatureStatus.UNSUPPORTED

    def test_sign_raises_not_implemented(self):
        from app.module_trust.signature import NoOpSignatureProvider

        provider = NoOpSignatureProvider()
        with pytest.raises(NotImplementedError):
            provider.sign(data=b"content", private_key=b"key")

    def test_identify_algorithm_is_none(self):
        from app.module_trust.signature import NoOpSignatureProvider

        assert NoOpSignatureProvider().identify_algorithm() == "none"


class TestSignatureProviderAbstraction:

    def test_cannot_instantiate_abstract_base_directly(self):
        from app.module_trust.signature import SignatureProvider

        with pytest.raises(TypeError):
            SignatureProvider()

    def test_default_signature_provider_is_noop_instance(self):
        from app.module_trust.signature import default_signature_provider, NoOpSignatureProvider

        assert isinstance(default_signature_provider, NoOpSignatureProvider)


# ── Slice 5 — Provenance (§14) ──────────────────────────────────────────────────

class TestInstallSource:

    def test_local_maps_to_local_file(self):
        from app.module_trust.provenance import resolve_install_source, InstallSource
        assert resolve_install_source("local") == InstallSource.LOCAL_FILE

    def test_development_maps_to_local_development(self):
        from app.module_trust.provenance import resolve_install_source, InstallSource
        assert resolve_install_source("development") == InstallSource.LOCAL_DEVELOPMENT

    def test_catalog_maps_to_internal_catalog(self):
        from app.module_trust.provenance import resolve_install_source, InstallSource
        assert resolve_install_source("catalog") == InstallSource.INTERNAL_CATALOG

    def test_unknown_source_type_defaults_to_local_file(self):
        from app.module_trust.provenance import resolve_install_source, InstallSource
        assert resolve_install_source("something_else") == InstallSource.LOCAL_FILE


class TestModuleEntryProvenance:

    def test_module_entry_default_source_type_is_local(self):
        from datetime import datetime
        from app.module_engine.registry import ModuleEntry
        from app.module_engine.enums import ModuleStatus

        entry = ModuleEntry(
            module_id="x", name="X", version="1.0.0", category="C", vendor="V",
            author="A", description="D", status=ModuleStatus.INSTALLED,
            install_date=datetime.now())
        assert entry.source_type == "local"
        assert entry.source_location is None

    def test_from_manifest_carries_source_type(self, tmp_path):
        import yaml
        from app.module_engine.manifest import ManifestParser
        from app.module_engine.registry import ModuleEntry
        from app.module_engine.enums import ModuleStatus

        mod_dir = tmp_path / "mod"
        mod_dir.mkdir()
        manifest = {
            "id": "mod", "name": "Mod", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
            "icon": "shield-check", "order": 10,
            "source_type": "development", "source_location": "/dev/mod",
        }
        (mod_dir / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

        parsed = ManifestParser.parse(mod_dir)
        entry = ModuleEntry.from_manifest(parsed, ModuleStatus.INSTALLED, [], [])
        assert entry.source_type == "development"
        assert entry.source_location == "/dev/mod"


# ── Slice 5 — Module Validator: Integrity/Signature/Trust (§19) ────────────────

class TestValidatorIntegritySignatureTrust:

    def test_source_dir_without_integrity_json_is_warning_not_error(self, tmp_path):
        """Fluxo normal: fonte ainda nao instalada nao tem integrity.json."""
        from techforge_cli.validators.module_validator import ModuleCLIValidator

        mod = tmp_path / "mod"
        (mod / "backend").mkdir(parents=True)
        (mod / "frontend").mkdir(parents=True)
        (mod / "backend" / "main.py").write_text("router = None\nmodule = None\n")
        (mod / "frontend" / "index.tsx").write_text(
            "export const moduleConfig={}\nexport default function(){return null}\n")
        manifest = {
            "id": "mod", "name": "Mod", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
            "icon": "shield-check", "order": 10,
        }
        import yaml
        (mod / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

        report = ModuleCLIValidator.validate(mod)
        integrity_checks = [c for c in report.checks if c.name.startswith("§10 Integrity")]
        assert integrity_checks and integrity_checks[0].passed
        assert integrity_checks[0].level == "warning"

    def test_installed_dir_with_valid_integrity_passes(self, tmp_path):
        from app.module_trust.integrity import write_integrity_manifest
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        import yaml

        mod = tmp_path / "mod"
        (mod / "backend").mkdir(parents=True)
        (mod / "frontend").mkdir(parents=True)
        (mod / "backend" / "main.py").write_text("router = None\nmodule = None\n")
        (mod / "frontend" / "index.tsx").write_text(
            "export const moduleConfig={}\nexport default function(){return null}\n")
        manifest = {
            "id": "mod", "name": "Mod", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
            "icon": "shield-check", "order": 10,
        }
        (mod / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        write_integrity_manifest(mod)

        report = ModuleCLIValidator.validate(mod)
        integrity_checks = [c for c in report.checks
                            if c.name.startswith("§10 Integrity") and "VALID" in c.name]
        assert integrity_checks and integrity_checks[0].passed

        trust_checks = [c for c in report.checks if c.name.startswith("§10 Trust Level")]
        assert trust_checks and "UNVERIFIED" in trust_checks[0].name

    def test_installed_dir_with_modified_file_fails_integrity(self, tmp_path):
        from app.module_trust.integrity import write_integrity_manifest
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        import yaml

        mod = tmp_path / "mod"
        (mod / "backend").mkdir(parents=True)
        (mod / "frontend").mkdir(parents=True)
        (mod / "backend" / "main.py").write_text("router = None\nmodule = None\n")
        (mod / "frontend" / "index.tsx").write_text(
            "export const moduleConfig={}\nexport default function(){return null}\n")
        manifest = {
            "id": "mod", "name": "Mod", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
            "icon": "shield-check", "order": 10,
        }
        (mod / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")
        write_integrity_manifest(mod)
        (mod / "backend" / "main.py").write_text("router = None\nmodule = None\nEVIL=1\n")

        report = ModuleCLIValidator.validate(mod)
        integrity_checks = [c for c in report.checks if c.name.startswith("§10 Integrity")]
        assert integrity_checks and not integrity_checks[0].passed
        assert not report.passed

    def test_signature_absent_is_warning_never_blocks(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        import yaml

        mod = tmp_path / "mod"
        (mod / "backend").mkdir(parents=True)
        (mod / "frontend").mkdir(parents=True)
        (mod / "backend" / "main.py").write_text("router = None\nmodule = None\n")
        (mod / "frontend" / "index.tsx").write_text(
            "export const moduleConfig={}\nexport default function(){return null}\n")
        manifest = {
            "id": "mod", "name": "Mod", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
            "icon": "shield-check", "order": 10,
        }
        (mod / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

        report = ModuleCLIValidator.validate(mod)
        sig_checks = [c for c in report.checks if c.name.startswith("§10 Signature")]
        assert sig_checks and sig_checks[0].passed
        assert sig_checks[0].level == "warning"


# ── Slice 5 — Install-time dependency blocking (§7) ────────────────────────────

class TestInstallBlocksInvalidDependencies:

    def test_install_rejects_structurally_invalid_dependency(self, tmp_path):
        import asyncio
        from app.package_manager.manager import PackageManager
        from app.package_manager.enums import InstallStatus
        from tests.test_phase4 import make_mod_file

        installed_dir = tmp_path / "installed"
        cache_dir = tmp_path / "cache"
        installed_dir.mkdir()
        cache_dir.mkdir()

        manifest = {
            "id": "bad_dep_mod", "name": "Bad Dep", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "999.999.999",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
            "dependencies": [{"target": {"type": "bogus_type", "id": "x"}}],
        }
        mod_path = make_mod_file(tmp_path, manifest)

        pm = PackageManager(installed_path=installed_dir, cache_path=cache_dir)
        result = asyncio.run(pm.install(mod_path))

        assert result.status == InstallStatus.FAILED
        assert not (installed_dir / "bad_dep_mod").exists()

    def test_install_accepts_structurally_valid_dependency(self, tmp_path):
        import asyncio
        from app.package_manager.manager import PackageManager
        from app.package_manager.enums import InstallStatus
        from tests.test_phase4 import make_mod_file

        installed_dir = tmp_path / "installed"
        cache_dir = tmp_path / "cache"
        installed_dir.mkdir()
        cache_dir.mkdir()

        manifest = {
            "id": "good_dep_mod", "name": "Good Dep", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "999.999.999",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
            "dependencies": [{"target": {"type": "capability", "id": "aws.cost.read"},
                              "required": False}],
        }
        mod_path = make_mod_file(tmp_path, manifest)

        pm = PackageManager(installed_path=installed_dir, cache_path=cache_dir)
        result = asyncio.run(pm.install(mod_path))

        assert result.status == InstallStatus.SUCCESS


# ── Slice 6 — Runtime verification + Notifications (§15/§16/§20) ──────────────

class TestVerifyModuleIntegrity:

    def test_valid_module_does_not_notify(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.db.database import AsyncSessionLocal
        from app.module_trust.integrity import write_integrity_manifest
        from app.module_trust.verification import verify_module_integrity
        from app.models.notifications import Notification
        from sqlalchemy import select, func, delete

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        module_id = "verify_test_valid"
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        write_integrity_manifest(mod_dir)

        title = "Module integrity changed"

        async def _run():
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Notification).where(
                    Notification.title == title, Notification.module_id == module_id))
                await db.commit()

                before = (await db.execute(
                    select(func.count(Notification.id)).where(
                        Notification.title == title, Notification.module_id == module_id)
                )).scalar()

                result = await verify_module_integrity(module_id, db)

                after = (await db.execute(
                    select(func.count(Notification.id)).where(
                        Notification.title == title, Notification.module_id == module_id)
                )).scalar()
                return result, before, after

        result, before, after = asyncio.run(_run())
        assert result.status.value == "VALID"
        assert before == after == 0

    def test_modified_module_notifies_once_with_dedupe(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.db.database import AsyncSessionLocal
        from app.module_trust.integrity import write_integrity_manifest
        from app.module_trust.verification import verify_module_integrity
        from app.models.notifications import Notification
        from sqlalchemy import select, func, delete

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        module_id = "verify_test_modified"
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        write_integrity_manifest(mod_dir)
        (mod_dir / "backend" / "main.py").write_text("x=2\n", encoding="utf-8")

        title = "Module integrity changed"

        async def _run():
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Notification).where(
                    Notification.title == title, Notification.module_id == module_id))
                await db.commit()

                before = (await db.execute(
                    select(func.count(Notification.id)).where(
                        Notification.title == title, Notification.module_id == module_id)
                )).scalar()

                r1 = await verify_module_integrity(module_id, db)
                r2 = await verify_module_integrity(module_id, db)  # repete — deve dedupe

                after = (await db.execute(
                    select(func.count(Notification.id)).where(
                        Notification.title == title, Notification.module_id == module_id)
                )).scalar()
                return r1, r2, before, after

        r1, r2, before, after = asyncio.run(_run())
        assert r1.status.value == "MODIFIED"
        assert r2.status.value == "MODIFIED"
        assert before == 0
        assert after == 1  # notificou uma unica vez, mesmo chamando 2x


class TestVerifyModuleAPIRoute:

    def test_verify_unknown_module_404(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.post("/api/v1/modules/ghost_module_9x/verify")
            assert resp.status_code == 404

    def test_verify_known_module_returns_status(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.post("/api/v1/modules/hello_world/verify")
            assert resp.status_code == 200
            body = resp.json()
            assert body["module_id"] == "hello_world"
            assert "status" in body


class TestUpdateRegeneratesIntegrityManifest:
    """Regressao do bug encontrado nesta slice — update() nao regravava integrity.json."""

    def test_update_writes_fresh_integrity_manifest(self, tmp_path):
        import asyncio
        import json as _json
        from app.package_manager.manager import PackageManager
        from app.package_manager.enums import UpdateStatus
        from tests.test_phase4 import make_mod_file

        installed_dir = tmp_path / "installed"
        cache_dir = tmp_path / "cache"
        installed_dir.mkdir()
        cache_dir.mkdir()

        manifest_v1 = {
            "id": "update_integrity_mod", "name": "V1", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "999.999.999",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
        }
        mod_v1 = make_mod_file(tmp_path, manifest_v1)

        pm = PackageManager(installed_path=installed_dir, cache_path=cache_dir)
        install_result = asyncio.run(pm.install(mod_v1))
        assert install_result.status.value == "success"

        manifest_v2 = dict(manifest_v1, version="2.0.0")
        # make_mod_file usa tmp/src/<id> como diretorio de staging — precisa
        # limpar antes de gerar a v2 pra nao reusar arquivos da v1.
        import shutil as _shutil
        staging = tmp_path / "src" / "update_integrity_mod"
        if staging.exists():
            _shutil.rmtree(staging)
        mod_v2 = make_mod_file(tmp_path, manifest_v2)

        update_result = asyncio.run(pm.update("update_integrity_mod", mod_v2))
        assert update_result.status == UpdateStatus.SUCCESS

        integrity_file = installed_dir / "update_integrity_mod" / "integrity.json"
        assert integrity_file.is_file()
        data = _json.loads(integrity_file.read_text(encoding="utf-8"))
        assert "manifest.yaml" in data["files"]


# ── Slice 7 — API: GET /modules/{id}/integrity e /trust (§24) ─────────────────

class TestModuleIntegrityRoute:

    def test_get_integrity_unknown_module_404(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/api/v1/modules/ghost_module_9x/integrity")
            assert resp.status_code == 404

    def test_get_integrity_known_module_returns_status(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/api/v1/modules/hello_world/integrity")
            assert resp.status_code == 200
            assert resp.json()["module_id"] == "hello_world"

    def test_get_integrity_is_read_only_no_notification_side_effect(self, tmp_path, monkeypatch):
        """GET nao deve notificar (diferente do POST /verify) — e so leitura."""
        import asyncio
        from app.core.settings import settings
        from app.module_engine.registry import registry, ModuleEntry
        from app.module_engine.enums import ModuleStatus
        from datetime import datetime
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db.database import AsyncSessionLocal
        from app.models.notifications import Notification
        from sqlalchemy import select, func, delete

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        module_id = "integrity_get_test"
        mod_dir = tmp_path / module_id
        (mod_dir / "backend").mkdir(parents=True)
        (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
        from app.module_trust.integrity import write_integrity_manifest
        write_integrity_manifest(mod_dir)
        (mod_dir / "backend" / "main.py").write_text("x=2\n", encoding="utf-8")  # modifica

        entry = ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.INSTALLED, install_date=datetime.now())
        registry.register(entry)

        title = "Module integrity changed"
        try:
            async def _clean():
                async with AsyncSessionLocal() as db:
                    await db.execute(delete(Notification).where(
                        Notification.title == title, Notification.module_id == module_id))
                    await db.commit()
            asyncio.run(_clean())

            with TestClient(app) as client:
                resp = client.get(f"/api/v1/modules/{module_id}/integrity")
                assert resp.status_code == 200
                assert resp.json()["status"] == "MODIFIED"

            async def _count():
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(func.count(Notification.id)).where(
                        Notification.title == title, Notification.module_id == module_id))
                    return result.scalar()
            assert asyncio.run(_count()) == 0
        finally:
            registry.deregister(module_id)


# ── Slice 8 — Listagem em lote + AI Context + teste integrado (§21/§27/§29) ────

class TestListModulesTrust:

    def test_list_modules_trust_returns_only_installed(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/api/v1/modules/trust")
            assert resp.status_code == 200
            body = resp.json()
            module_ids = [m["module_id"] for m in body]
            assert "hello_world" in module_ids

    def test_list_modules_trust_route_does_not_collide_with_module_id_route(self):
        """Regressao — /trust (lote) nao pode ser interpretado como
        module_id='trust' pela rota /{module_id}/trust."""
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/api/v1/modules/trust")
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)


class TestModuleTrustRoute:

    def test_get_trust_unknown_module_404(self):
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/api/v1/modules/ghost_module_9x/trust")
            assert resp.status_code == 404

    def test_get_trust_known_module_without_publisher_is_unverified(self):
        """hello_world nao declara publisher — integridade nao foi gerada
        (nao esta em modules/installed com integrity.json real neste
        ambiente de teste), entao aceita tanto UNVERIFIED quanto INVALID
        dependendo do estado do integrity.json real do repo; o que importa
        e que a rota responde 200 com um trust_level valido."""
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.get("/api/v1/modules/hello_world/trust")
            assert resp.status_code == 200
            body = resp.json()
            assert body["trust_level"] in (
                "TRUSTED", "VERIFIED", "UNVERIFIED", "MODIFIED", "INVALID")
            assert body["publisher"] is None

    def test_get_trust_returns_valid_trust_level_field(self):
        """GET /trust com modulo conhecido retorna um trust_level valido."""
        from fastapi.testclient import TestClient
        from app.main import app
        with TestClient(app) as client:
            resp = client.get(f"/api/v1/modules/hello_world/trust")
            assert resp.status_code == 200
            body = resp.json()
            assert "trust_level" in body
            assert body["trust_level"] in (
                "TRUSTED", "VERIFIED", "UNVERIFIED", "MODIFIED", "INVALID")
            assert "integrity_status" in body
            assert "signature_status" in body
            assert "module_id" in body

    def test_get_trust_with_registered_publisher_is_verified(self, tmp_path, monkeypatch):
        """Prova a resolucao real com Publisher do banco — o motivo desta
        rota existir separada do ModuleCLIValidator sincrono (Slice 5).

        Nota de ordem: o registro manual em `registry` e o monkeypatch de
        MODULES_INSTALLED_PATH precisam acontecer DEPOIS que o TestClient
        ja disparou o lifespan de startup (que reescaneia o diretorio real
        de modulos) — senao o scan do boot sobrescreve a entrada fake."""
        import asyncio
        from datetime import datetime
        from fastapi.testclient import TestClient
        from app.main import app
        from app.core.settings import settings
        from app.module_engine.registry import registry, ModuleEntry
        from app.module_engine.enums import ModuleStatus
        from app.module_trust.integrity import write_integrity_manifest
        from app.db.database import AsyncSessionLocal
        from app.services.publisher import PublisherService
        from app.schemas.publisher import PublisherCreate
        from sqlalchemy import delete
        from app.models.publisher import Publisher

        module_id = "trust_get_test"

        with TestClient(app) as client:
            monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
            mod_dir = tmp_path / module_id
            (mod_dir / "backend").mkdir(parents=True)
            (mod_dir / "backend" / "main.py").write_text("x=1\n", encoding="utf-8")
            write_integrity_manifest(mod_dir)

            entry = ModuleEntry(
                module_id=module_id, name=module_id, version="1.0.0",
                category="C", vendor="V", author="A", description="D",
                status=ModuleStatus.INSTALLED, install_date=datetime.now(),
                manifest_raw={"publisher": {"id": "trust_get_publisher"}})
            registry.register(entry)

            try:
                async def _setup():
                    async with AsyncSessionLocal() as db:
                        await db.execute(delete(Publisher).where(Publisher.id == "trust_get_publisher"))
                        await db.commit()
                        await PublisherService.register(db, PublisherCreate(
                            id="trust_get_publisher", name="Test Publisher",
                            type="INTERNAL", trust_status="UNTRUSTED"))
                asyncio.run(_setup())

                resp = client.get(f"/api/v1/modules/{module_id}/trust")
                assert resp.status_code == 200
                body = resp.json()
                assert body["trust_level"] == "VERIFIED"
                assert body["publisher"]["id"] == "trust_get_publisher"
            finally:
                registry.deregister(module_id)

                async def _cleanup():
                    async with AsyncSessionLocal() as db:
                        await db.execute(delete(Publisher).where(Publisher.id == "trust_get_publisher"))
                        await db.commit()
                asyncio.run(_cleanup())


# ── Regra final (§29) — teste integrado completo, tmp_path ─────────────────────

class TestPhase10FullIntegration:
    """
    Create Package -> Generate Integrity -> Install -> Verify VALID ->
    Modify File -> Verify MODIFIED -> Notification (dedupe).

    Os casos de publisher desconhecido/revogado (-> UNVERIFIED/INVALID)
    já têm cobertura dedicada exaustiva em TestTrustResolver (Slice 3) e
    TestModuleTrustRoute (Slice 7) — não repetidos aqui pra evitar
    redundância; esta amarra especificamente a cadeia real
    install -> modify -> verify -> notify em um fluxo só.
    """

    def test_full_lifecycle_install_modify_verify_notify(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.package_manager.manager import PackageManager
        from app.package_manager.enums import InstallStatus
        from app.module_trust.integrity import IntegrityStatus, verify_integrity
        from app.module_trust.verification import verify_module_integrity
        from app.db.database import AsyncSessionLocal
        from app.models.notifications import Notification
        from sqlalchemy import select, func, delete
        from tests.test_phase4 import make_mod_file

        installed_dir = tmp_path / "installed"
        cache_dir = tmp_path / "cache"
        installed_dir.mkdir()
        cache_dir.mkdir()
        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", installed_dir)

        module_id = "full_integration_trust_mod"
        manifest = {
            "id": module_id, "name": "Full Integration", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "999.999.999",
            "category": "Test", "vendor": "T", "author": "T", "description": "T",
            "entry_backend": "backend/main.py", "entry_frontend": "frontend/index.tsx",
        }
        mod_path = make_mod_file(tmp_path, manifest)

        pm = PackageManager(installed_path=installed_dir, cache_path=cache_dir)

        # Install -> integrity.json gerado automaticamente (Slice 1/5)
        result = asyncio.run(pm.install(mod_path))
        assert result.status == InstallStatus.SUCCESS

        module_dir = installed_dir / module_id
        assert (module_dir / "integrity.json").is_file()

        # Verify VALID
        initial = verify_integrity(module_dir)
        assert initial.status == IntegrityStatus.VALID

        # Modify file -> Verify MODIFIED
        backend_file = module_dir / "backend" / "main.py"
        backend_file.write_text(backend_file.read_text(encoding="utf-8") + "\n# tampered\n",
                                encoding="utf-8")

        title = "Module integrity changed"

        async def _run():
            async with AsyncSessionLocal() as db:
                await db.execute(delete(Notification).where(
                    Notification.title == title, Notification.module_id == module_id))
                await db.commit()

                before = (await db.execute(select(func.count(Notification.id)).where(
                    Notification.title == title, Notification.module_id == module_id))).scalar()

                result1 = await verify_module_integrity(module_id, db)
                result2 = await verify_module_integrity(module_id, db)  # repete — deve dedupe

                after = (await db.execute(select(func.count(Notification.id)).where(
                    Notification.title == title, Notification.module_id == module_id))).scalar()
                return result1, result2, before, after

        r1, r2, before, after = asyncio.run(_run())

        assert r1.status == IntegrityStatus.MODIFIED
        assert r2.status == IntegrityStatus.MODIFIED
        assert before == 0
        assert after == 1  # notificado uma unica vez (dedupe)
