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
