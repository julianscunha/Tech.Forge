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
