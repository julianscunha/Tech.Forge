"""
TechForge Phase 4 — Package Manager Test Suite
================================================
Tests:  install, remove, update, compatibility, validation, manual import,
        operation log, repository provider, hot-reload flow.

Run:  pytest core/backend/tests/test_phase4.py -v
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))

from app.package_manager.compatibility import check_compatibility
from app.package_manager.enums import (
    CompatibilityLevel, InstallStatus, RemoveStatus, UpdateStatus,
)
from app.package_manager.models import PackageInfo
from app.package_manager.operation_log import OperationLog
from app.package_manager.repository import LocalRepositoryProvider


# ── Fixtures ──────────────────────────────────────────────────────────────────

MANIFEST_BASE = {
    "id": "test_pkg",
    "name": "Test Package",
    "version": "1.0.0",
    "platform_min_version": "1.0.0",
    "platform_max_version": "2.0.0",
    "category": "Test",
    "vendor": "TechForge",
    "author": "Tester",
    "description": "A test package.",
    "entry_backend": "backend/main.py",
    "entry_frontend": "frontend/index.tsx",
    "icon": "shield-check",
    "order": 10,
}


def make_mod_file(tmp: Path, manifest: dict) -> Path:
    """Create a minimal valid .mod file in tmp/."""
    mod_dir = tmp / "src" / manifest["id"]
    (mod_dir / "backend").mkdir(parents=True)
    (mod_dir / "frontend").mkdir(parents=True)
    (mod_dir / "backend" / "main.py").write_text(
        "from fastapi import APIRouter\nfrom techforge_sdk.contracts import ModuleContract\nrouter=APIRouter()\n"
    )
    (mod_dir / "frontend" / "index.tsx").write_text(
        "export const moduleConfig={}\nexport default function P(){return null}\n"
    )
    (mod_dir / "manifest.yaml").write_text(yaml.dump(manifest), encoding="utf-8")

    mod_path = tmp / f"{manifest['id']}-{manifest['version']}.mod"
    with zipfile.ZipFile(mod_path, "w") as zf:
        for f in mod_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(mod_dir))
        zf.writestr("META-INF/TECHFORGE", "TECHFORGE_MODULE_FORMAT=1.0\n")
        zf.writestr("META-INF/BUILD", json.dumps({
            "module_id": manifest["id"],
            "version": manifest["version"],
            "format": "techforge-mod-v1",
        }))
    return mod_path


def make_package_manager(tmp: Path):
    from app.package_manager.manager import PackageManager
    installed = tmp / "installed"
    cache     = tmp / "cache"
    repo_path = tmp / "repository"
    installed.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    repo_path.mkdir(parents=True, exist_ok=True)
    provider = LocalRepositoryProvider(
        repository_path=repo_path,
        cache_path=cache,
    )
    return PackageManager(
        installed_path=installed,
        cache_path=cache,
        repository=provider,
        use_global_registry=False,  # testes isolados: registry próprio
    )


# ── Compatibility tests ───────────────────────────────────────────────────────

class TestCompatibility:

    def test_compatible(self):
        assert check_compatibility("1.0.0", "1.0.0", "2.0.0") == CompatibilityLevel.COMPATIBLE

    def test_compatible_middle(self):
        assert check_compatibility("1.5.0", "1.0.0", "2.0.0") == CompatibilityLevel.COMPATIBLE

    def test_incompatible_below(self):
        assert check_compatibility("0.9.0", "1.0.0", "2.0.0") == CompatibilityLevel.INCOMPATIBLE

    def test_incompatible_above(self):
        assert check_compatibility("3.0.0", "1.0.0", "2.0.0") == CompatibilityLevel.INCOMPATIBLE

    def test_warning_near_max(self):
        # platform 1.9.0, max 1.10.0 → same major, minor differs by 1 → WARNING
        result = check_compatibility("1.9.0", "1.0.0", "1.10.0")
        assert result == CompatibilityLevel.WARNING

    def test_exact_min(self):
        assert check_compatibility("1.0.0", "1.0.0", "1.0.0") == CompatibilityLevel.COMPATIBLE

    def test_exact_max(self):
        assert check_compatibility("2.0.0", "1.0.0", "2.0.0") == CompatibilityLevel.COMPATIBLE

    def test_open_range(self):
        assert check_compatibility("99.0.0", "0.0.0", "999.999.999") == CompatibilityLevel.COMPATIBLE


# ── Install tests ─────────────────────────────────────────────────────────────

class TestInstall:

    def test_install_valid_mod(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
        result = asyncio.run(pm.install(mod))
        assert result.success, result.message
        assert result.status == InstallStatus.SUCCESS
        assert (tmp_path / "installed" / "test_pkg").exists()

    def test_install_creates_module_dir(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
        asyncio.run(pm.install(mod))
        assert (tmp_path / "installed" / "test_pkg" / "manifest.yaml").exists()
        assert (tmp_path / "installed" / "test_pkg" / "backend" / "main.py").exists()

    def test_install_nonexistent_file_fails(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        result = asyncio.run(pm.install(tmp_path / "ghost.mod"))
        assert not result.success
        assert result.status == InstallStatus.FAILED

    def test_install_not_a_zip_fails(self, tmp_path):
        bad = tmp_path / "bad.mod"
        bad.write_text("not a zip")
        pm  = make_package_manager(tmp_path)
        result = asyncio.run(pm.install(bad))
        assert not result.success

    def test_install_missing_manifest_fails(self, tmp_path):
        mod_path = tmp_path / "no_manifest-1.0.0.mod"
        with zipfile.ZipFile(mod_path, "w") as zf:
            zf.writestr("backend/main.py", "# empty")
        pm = make_package_manager(tmp_path)
        result = asyncio.run(pm.install(mod_path))
        assert not result.success

    def test_install_duplicate_fails(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
        asyncio.run(pm.install(mod))
        mod2 = make_mod_file(tmp_path / "second", MANIFEST_BASE.copy())
        result = asyncio.run(pm.install(mod2))
        assert result.status == InstallStatus.ALREADY_INSTALLED

    def test_install_incompatible_blocked(self, tmp_path):
        m = {**MANIFEST_BASE, "platform_min_version": "9.0.0", "platform_max_version": "10.0.0"}
        pm  = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, m)
        result = asyncio.run(pm.install(mod))
        assert result.status == InstallStatus.INCOMPATIBLE
        assert not (tmp_path / "installed" / "test_pkg").exists()

    def test_install_logs_operation(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
        from app.package_manager.operation_log import operation_log
        before = len(operation_log.all())
        asyncio.run(pm.install(mod))
        assert len(operation_log.all()) > before


# ── Remove tests ──────────────────────────────────────────────────────────────

class TestRemove:

    def _install(self, pm, tmp_path, manifest=None):
        m = manifest or MANIFEST_BASE.copy()
        mod = make_mod_file(tmp_path, m)
        asyncio.run(pm.install(mod))

    def test_remove_installed_module(self, tmp_path):
        pm = make_package_manager(tmp_path)
        self._install(pm, tmp_path)
        result = asyncio.run(pm.remove("test_pkg"))
        assert result.success
        assert not (tmp_path / "installed" / "test_pkg").exists()

    def test_remove_not_installed_fails(self, tmp_path):
        pm = make_package_manager(tmp_path)
        result = asyncio.run(pm.remove("ghost_pkg"))
        assert result.status == RemoveStatus.NOT_FOUND

    def test_remove_cleans_directory(self, tmp_path):
        pm = make_package_manager(tmp_path)
        self._install(pm, tmp_path)
        asyncio.run(pm.remove("test_pkg"))
        assert not (tmp_path / "installed" / "test_pkg").is_dir()

    def test_remove_logs_operation(self, tmp_path):
        pm = make_package_manager(tmp_path)
        self._install(pm, tmp_path)
        from app.package_manager.operation_log import operation_log
        asyncio.run(pm.remove("test_pkg"))
        log_entry = next(
            (e for e in operation_log.all() if e.operation == "remove" and e.module_id == "test_pkg"),
            None
        )
        assert log_entry is not None


# ── Update tests ──────────────────────────────────────────────────────────────

class TestUpdate:

    def test_update_to_newer_version(self, tmp_path):
        pm = make_package_manager(tmp_path)
        v1 = make_mod_file(tmp_path / "v1", MANIFEST_BASE.copy())
        asyncio.run(pm.install(v1))

        m2 = {**MANIFEST_BASE, "version": "2.0.0"}
        v2 = make_mod_file(tmp_path / "v2", m2)
        result = asyncio.run(pm.update("test_pkg", v2))
        assert result.success, result.message
        assert result.to_version == "2.0.0"

    def test_update_same_version_returns_up_to_date(self, tmp_path):
        pm = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path / "v1", MANIFEST_BASE.copy())
        asyncio.run(pm.install(mod))
        mod2 = make_mod_file(tmp_path / "v2", MANIFEST_BASE.copy())
        result = asyncio.run(pm.update("test_pkg", mod2))
        assert result.status == UpdateStatus.UP_TO_DATE

    def test_update_older_version_returns_up_to_date(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        v2  = make_mod_file(tmp_path / "v2", {**MANIFEST_BASE, "version": "2.0.0"})
        asyncio.run(pm.install(v2))
        v1  = make_mod_file(tmp_path / "v1", MANIFEST_BASE.copy())
        result = asyncio.run(pm.update("test_pkg", v1))
        assert result.status == UpdateStatus.UP_TO_DATE

    def test_update_incompatible_blocked(self, tmp_path):
        pm = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path / "v1", MANIFEST_BASE.copy())
        asyncio.run(pm.install(mod))
        m2 = {**MANIFEST_BASE, "version": "2.0.0",
              "platform_min_version": "9.0.0", "platform_max_version": "10.0.0"}
        bad = make_mod_file(tmp_path / "v2", m2)
        result = asyncio.run(pm.update("test_pkg", bad))
        assert result.status == UpdateStatus.INCOMPATIBLE

    def test_update_not_installed_returns_not_found(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, {**MANIFEST_BASE, "version": "2.0.0"})
        result = asyncio.run(pm.update("ghost_pkg", mod))
        assert result.status == UpdateStatus.NOT_FOUND

    def test_update_creates_backup(self, tmp_path):
        pm = make_package_manager(tmp_path)
        v1 = make_mod_file(tmp_path / "v1", MANIFEST_BASE.copy())
        asyncio.run(pm.install(v1))
        v2 = make_mod_file(tmp_path / "v2", {**MANIFEST_BASE, "version": "2.0.0"})
        asyncio.run(pm.update("test_pkg", v2))
        backup = tmp_path / "cache" / "test_pkg-1.0.0.bak"
        assert backup.exists()


# ── Package Manager query tests ───────────────────────────────────────────────

class TestPackageManagerQueries:

    def test_list_installed_empty_initially(self, tmp_path):
        pm = make_package_manager(tmp_path)
        result = asyncio.run(pm.list_installed())
        assert result == []

    def test_list_available_empty_with_no_repo(self, tmp_path):
        pm = make_package_manager(tmp_path)
        result = asyncio.run(pm.list_available())
        assert result == []

    def test_list_available_finds_mod_files(self, tmp_path):
        pm  = make_package_manager(tmp_path)
        mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
        shutil.copy(mod, tmp_path / "repository" / mod.name)
        result = asyncio.run(pm.list_available())
        assert len(result) == 1
        assert result[0].module_id == "test_pkg"

    def test_list_updates_detects_newer(self, tmp_path):
        pm = make_package_manager(tmp_path)
        # Install v1
        v1 = make_mod_file(tmp_path / "install", MANIFEST_BASE.copy())
        asyncio.run(pm.install(v1))
        # Put v2 in repository
        v2 = make_mod_file(tmp_path / "repo", {**MANIFEST_BASE, "version": "2.0.0"})
        shutil.copy(v2, tmp_path / "repository" / v2.name)
        result = asyncio.run(pm.list_updates())
        assert len(result) == 1
        assert result[0].version == "2.0.0"


# ── Local Repository Provider tests ──────────────────────────────────────────

class TestLocalRepositoryProvider:

    def test_list_available_finds_mods(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        cache = tmp_path / "cache"
        cache.mkdir()
        mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
        shutil.copy(mod, repo / mod.name)
        provider = LocalRepositoryProvider(repo, cache)
        result = asyncio.run(provider.list_available("1.0.0"))
        assert len(result) == 1
        assert result[0].module_id == "test_pkg"

    def test_get_package_returns_correct(self, tmp_path):
        repo  = tmp_path / "repo"
        repo.mkdir()
        cache = tmp_path / "cache"
        cache.mkdir()
        mod = make_mod_file(tmp_path, MANIFEST_BASE.copy())
        shutil.copy(mod, repo / mod.name)
        provider = LocalRepositoryProvider(repo, cache)
        result = asyncio.run(provider.get_package("test_pkg", "1.0.0"))
        assert result is not None
        assert result.version == "1.0.0"

    def test_get_package_missing_returns_none(self, tmp_path):
        repo  = tmp_path / "repo"
        repo.mkdir()
        cache = tmp_path / "cache"
        cache.mkdir()
        provider = LocalRepositoryProvider(repo, cache)
        result = asyncio.run(provider.get_package("missing", "1.0.0"))
        assert result is None

    def test_store_upload_saves_file(self, tmp_path):
        repo  = tmp_path / "repo"
        repo.mkdir()
        cache = tmp_path / "cache"
        cache.mkdir()
        provider = LocalRepositoryProvider(repo, cache)
        content = b"fake mod content"
        path = asyncio.run(provider.store_upload("test.mod", content))
        assert path.exists()
        assert path.read_bytes() == content


# ── PackageInfo model tests ───────────────────────────────────────────────────

class TestPackageInfo:

    def test_has_update_true_when_newer_available(self):
        pkg = PackageInfo(
            module_id="x", name="X", version="2.0.0",
            category="T", vendor="T", author="T", description="T",
            is_installed=True, installed_version="1.0.0",
        )
        assert pkg.has_update is True

    def test_has_update_false_when_same(self):
        pkg = PackageInfo(
            module_id="x", name="X", version="1.0.0",
            category="T", vendor="T", author="T", description="T",
            is_installed=True, installed_version="1.0.0",
        )
        assert pkg.has_update is False

    def test_has_update_false_when_not_installed(self):
        pkg = PackageInfo(
            module_id="x", name="X", version="2.0.0",
            category="T", vendor="T", author="T", description="T",
            is_installed=False,
        )
        assert pkg.has_update is False

    def test_from_manifest_dict(self):
        pkg = PackageInfo.from_manifest_dict(MANIFEST_BASE, platform_version="1.0.0")
        assert pkg.module_id == "test_pkg"
        assert pkg.compatibility == CompatibilityLevel.COMPATIBLE


# ── Operation Log tests ───────────────────────────────────────────────────────

class TestOperationLog:

    def test_records_entry(self):
        log = OperationLog()
        log.record("install", "mod_x", "1.0.0", "success", "Installed OK")
        assert len(log.all()) == 1

    def test_recent_returns_n(self):
        log = OperationLog()
        for i in range(10):
            log.record("install", f"mod_{i}", "1.0.0", "success", "OK")
        assert len(log.recent(5)) == 5

    def test_for_module_filters(self):
        log = OperationLog()
        log.record("install", "mod_a", "1.0.0", "success", "OK")
        log.record("install", "mod_b", "1.0.0", "success", "OK")
        assert len(log.for_module("mod_a")) == 1

    def test_respects_max_entries(self):
        log = OperationLog()
        log.MAX_ENTRIES = 5
        for i in range(10):
            log.record("install", f"mod_{i}", "1.0.0", "success", "OK")
        assert len(log.all()) == 5
