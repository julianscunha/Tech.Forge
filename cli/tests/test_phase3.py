"""
TechForge CLI — Automated Test Suite
======================================
Tests for: CLI commands, ManifestParser, ModuleValidator,
           TemplateGenerator, PackageBuilder, SDK Contracts.

Run with:  pytest cli/tests/ -v
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
import yaml

# Add SDK and CLI to path for testing
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "sdk" / "python"))
sys.path.insert(0, str(ROOT / "cli"))

from techforge_cli.packager.builder import PackageBuilder
from techforge_cli.templates.generator import ModuleSpec, TemplateGenerator
from techforge_cli.validators.module_validator import ModuleCLIValidator
from techforge_sdk import TechForgeSDK, create_sdk
from techforge_sdk.contracts import HealthResult, ModuleContract, ModuleMetadata

pytestmark = pytest.mark.integration


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_valid_module(tmp: Path, module_id: str = "test_mod") -> Path:
    """Create a minimal valid module directory for testing."""
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

    # §16 Documentation First Principle — every module needs overview.md
    # and at least one example (basic.md), regardless of module_type.
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


# ── ModuleCLIValidator tests ──────────────────────────────────────────────────

class TestModuleCLIValidator:

    def test_valid_module_passes(self, tmp_path):
        mod = make_valid_module(tmp_path)
        report = ModuleCLIValidator.validate(mod, "1.0.0")
        assert report.passed, f"Expected pass, errors: {[c.message for c in report.checks if not c.passed and c.level == 'error']}"

    def test_missing_directory_fails(self, tmp_path):
        report = ModuleCLIValidator.validate(tmp_path / "nonexistent")
        assert not report.passed
        assert any("not found" in c.message for c in report.checks)

    def test_missing_manifest_fails(self, tmp_path):
        mod = tmp_path / "no_manifest"
        mod.mkdir()
        report = ModuleCLIValidator.validate(mod)
        assert not report.passed
        assert any("manifest.yaml" in c.message for c in report.checks)

    def test_invalid_yaml_fails(self, tmp_path):
        mod = tmp_path / "bad_yaml"
        mod.mkdir()
        (mod / "manifest.yaml").write_text("{{{{invalid yaml", encoding="utf-8")
        report = ModuleCLIValidator.validate(mod)
        assert not report.passed

    def test_missing_required_fields_fails(self, tmp_path):
        mod = tmp_path / "missing_fields"
        mod.mkdir()
        (mod / "manifest.yaml").write_text(yaml.dump({"id": "x"}), encoding="utf-8")
        report = ModuleCLIValidator.validate(mod)
        assert not report.passed
        assert any("Missing" in c.message for c in report.checks)

    def test_invalid_id_format_fails(self, tmp_path):
        mod = make_valid_module(tmp_path, "test_mod")
        # Overwrite manifest with bad id
        manifest_data = yaml.safe_load((mod / "manifest.yaml").read_text())
        manifest_data["id"] = "Bad-ID!"
        (mod / "manifest.yaml").write_text(yaml.dump(manifest_data))
        report = ModuleCLIValidator.validate(mod)
        id_check = next((c for c in report.checks if "id format" in c.name.lower()), None)
        assert id_check and not id_check.passed

    def test_incompatible_platform_fails(self, tmp_path):
        mod = make_valid_module(tmp_path)
        manifest_data = yaml.safe_load((mod / "manifest.yaml").read_text())
        manifest_data["platform_min_version"] = "9.0.0"
        manifest_data["platform_max_version"] = "10.0.0"
        (mod / "manifest.yaml").write_text(yaml.dump(manifest_data))
        report = ModuleCLIValidator.validate(mod, "1.0.0")
        compat_check = next((c for c in report.checks if "compat" in c.name.lower()), None)
        assert compat_check and not compat_check.passed

    def test_missing_backend_subdir_fails(self, tmp_path):
        mod = make_valid_module(tmp_path)
        import shutil
        shutil.rmtree(mod / "backend")
        report = ModuleCLIValidator.validate(mod)
        assert not report.passed
        assert any("backend" in c.name.lower() and not c.passed for c in report.checks)

    def test_missing_entry_point_fails(self, tmp_path):
        mod = make_valid_module(tmp_path)
        (mod / "backend" / "main.py").unlink()
        report = ModuleCLIValidator.validate(mod)
        assert not report.passed
        assert any("entry_backend" in c.name and not c.passed for c in report.checks)

    def test_valid_module_has_no_errors(self, tmp_path):
        mod = make_valid_module(tmp_path)
        report = ModuleCLIValidator.validate(mod)
        assert report.error_count == 0


# ── TemplateGenerator tests ───────────────────────────────────────────────────

class TestTemplateGenerator:

    def _spec(self, module_id: str = "my_module") -> ModuleSpec:
        return ModuleSpec(
            id=module_id,
            name="My Module",
            category="Backup",
            vendor="ACME",
            author="Dev",
            description="A test module.",
        )

    def test_generates_required_files(self, tmp_path):
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(self._spec())

        assert (mod / "manifest.yaml").exists()
        assert (mod / "backend" / "main.py").exists()
        assert (mod / "frontend" / "index.tsx").exists()
        assert (mod / "docs" / "README.md").exists()
        assert (mod / "tests" / "test_module.py").exists()

    def test_generates_required_directories(self, tmp_path):
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(self._spec())

        for subdir in ("backend", "frontend", "assets", "docs", "tests"):
            assert (mod / subdir).is_dir(), f"{subdir}/ missing"

    def test_manifest_contains_spec_values(self, tmp_path):
        spec = self._spec("my_module")
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(spec)

        raw = yaml.safe_load((mod / "manifest.yaml").read_text())
        assert raw["id"]       == spec.id
        assert raw["name"]     == spec.name
        assert raw["category"] == spec.category
        assert raw["vendor"]   == spec.vendor

    def test_generated_module_passes_validation(self, tmp_path):
        gen = TemplateGenerator(tmp_path)
        mod = gen.generate(self._spec())
        report = ModuleCLIValidator.validate(mod)
        errors = [c for c in report.checks if not c.passed and c.level == "error"]
        assert not errors, f"Generated module has errors: {[c.message for c in errors]}"

    def test_duplicate_module_raises(self, tmp_path):
        gen = TemplateGenerator(tmp_path)
        gen.generate(self._spec())
        with pytest.raises(FileExistsError):
            gen.generate(self._spec())

    def test_spec_validates_bad_id(self):
        spec = ModuleSpec(id="Bad ID!", name="X", category="X", vendor="X",
                          author="X", description="X")
        assert spec.validate()

    def test_spec_validates_good_id(self):
        spec = ModuleSpec(id="my_module", name="X", category="X", vendor="X",
                          author="X", description="X")
        assert not spec.validate()


# ── PackageBuilder tests ──────────────────────────────────────────────────────

class TestPackageBuilder:

    def test_builds_mod_file(self, tmp_path):
        mod = make_valid_module(tmp_path / "src")
        out = tmp_path / "dist"
        result = PackageBuilder.build(mod, out)

        assert result.output_path.exists()
        assert result.output_path.suffix == ".mod"

    def test_output_named_correctly(self, tmp_path):
        mod = make_valid_module(tmp_path / "src")
        result = PackageBuilder.build(mod, tmp_path / "dist")
        assert result.module_id in result.output_path.name
        assert result.version   in result.output_path.name

    def test_checksum_file_created(self, tmp_path):
        mod = make_valid_module(tmp_path / "src")
        result = PackageBuilder.build(mod, tmp_path / "dist")
        sha_file = Path(str(result.output_path) + ".sha256")
        assert sha_file.exists()
        assert result.checksum in sha_file.read_text()

    def test_archive_contains_manifest(self, tmp_path):
        import zipfile
        mod = make_valid_module(tmp_path / "src")
        result = PackageBuilder.build(mod, tmp_path / "dist")
        with zipfile.ZipFile(result.output_path) as zf:
            names = zf.namelist()
        assert "manifest.yaml" in names

    def test_archive_contains_meta_inf(self, tmp_path):
        import zipfile
        mod = make_valid_module(tmp_path / "src")
        result = PackageBuilder.build(mod, tmp_path / "dist")
        with zipfile.ZipFile(result.output_path) as zf:
            names = zf.namelist()
        assert "META-INF/TECHFORGE" in names
        assert "META-INF/BUILD"     in names

    def test_file_count_positive(self, tmp_path):
        mod = make_valid_module(tmp_path / "src")
        result = PackageBuilder.build(mod, tmp_path / "dist")
        assert result.file_count > 0

    def test_missing_manifest_raises(self, tmp_path):
        mod = tmp_path / "empty"
        mod.mkdir()
        with pytest.raises(FileNotFoundError):
            PackageBuilder.build(mod, tmp_path / "dist")


# ── SDK Contracts tests ───────────────────────────────────────────────────────

class TestSDKContracts:

    def _make_concrete_module(self) -> ModuleContract:
        """Create a minimal concrete ModuleContract for testing."""

        class ConcreteModule(ModuleContract):
            @property
            def metadata(self):
                return ModuleMetadata(
                    id="test", name="Test", version="1.0.0",
                    category="Test", vendor="Test",
                    author="Test", description="Test",
                )
            async def install(self):    pass
            async def enable(self):     pass
            async def disable(self):    pass
            async def upgrade(self, v): pass
            async def health_check(self): return HealthResult.ok()
            async def uninstall(self):  pass

        return ConcreteModule()

    def test_abstract_class_not_instantiable(self):
        with pytest.raises(TypeError):
            ModuleContract()  # type: ignore

    def test_concrete_implementation_instantiable(self):
        mod = self._make_concrete_module()
        assert mod is not None

    def test_metadata_fields(self):
        mod = self._make_concrete_module()
        m = mod.metadata
        assert m.id and m.name and m.version and m.category

    def test_lifecycle_hooks_run(self):
        mod = self._make_concrete_module()
        asyncio.run(mod.install())
        asyncio.run(mod.enable())
        asyncio.run(mod.disable())
        asyncio.run(mod.upgrade("0.9.0"))
        asyncio.run(mod.uninstall())

    def test_health_result_ok(self):
        result = HealthResult.ok("All good", count=3)
        assert result.is_healthy
        assert result.details["count"] == 3

    def test_health_result_fail(self):
        result = HealthResult.fail("DB down", code=503)
        assert not result.is_healthy
        assert result.details["code"] == 503


# ── SDK Services tests ────────────────────────────────────────────────────────

class TestSDKServices:

    def test_create_sdk_returns_instance(self):
        sdk = create_sdk("test_module")
        assert isinstance(sdk, TechForgeSDK)

    def test_sdk_has_all_services(self):
        sdk = create_sdk("test_module")
        assert sdk.database
        assert sdk.storage
        assert sdk.logger
        assert sdk.settings
        assert sdk.notifications

    def test_settings_set_get(self, tmp_path):
        from techforge_sdk.settings import SettingsSDK
        s = SettingsSDK("test", tmp_path)
        s.set("key", "value")
        assert s.get("key") == "value"

    def test_settings_default_value(self, tmp_path):
        from techforge_sdk.settings import SettingsSDK
        s = SettingsSDK("test", tmp_path)
        assert s.get("missing", "default") == "default"

    def test_settings_delete(self, tmp_path):
        from techforge_sdk.settings import SettingsSDK
        s = SettingsSDK("test", tmp_path)
        s.set("k", "v")
        s.delete("k")
        assert s.get("k") is None

    def test_settings_persist(self, tmp_path):
        from techforge_sdk.settings import SettingsSDK
        s1 = SettingsSDK("test", tmp_path)
        s1.set("persistent", 42)
        s2 = SettingsSDK("test", tmp_path)   # new instance, same file
        assert s2.get("persistent") == 42

    def test_storage_write_read(self, tmp_path):
        from techforge_sdk.storage import StorageSDK
        s = StorageSDK("test", tmp_path)
        s.write("hello.txt", b"hello world")
        assert s.read("hello.txt") == b"hello world"

    def test_storage_exists(self, tmp_path):
        from techforge_sdk.storage import StorageSDK
        s = StorageSDK("test", tmp_path)
        assert not s.exists("nope.txt")
        s.write("yes.txt", b"x")
        assert s.exists("yes.txt")

    def test_storage_delete(self, tmp_path):
        from techforge_sdk.storage import StorageSDK
        s = StorageSDK("test", tmp_path)
        s.write("del.txt", b"x")
        s.delete("del.txt")
        assert not s.exists("del.txt")

    def test_storage_list(self, tmp_path):
        from techforge_sdk.storage import StorageSDK
        s = StorageSDK("test", tmp_path)
        s.write("a.txt", b"a")
        s.write("b.txt", b"b")
        files = s.list()
        assert "a.txt" in files
        assert "b.txt" in files

    def test_storage_path_traversal_blocked(self, tmp_path):
        from techforge_sdk.storage import StorageSDK
        s = StorageSDK("test", tmp_path)
        with pytest.raises(PermissionError):
            s.read("../../etc/passwd")

    def test_database_mock_insert_fetch(self):
        import asyncio

        from techforge_sdk.database import DatabaseSDK
        db = DatabaseSDK("test")
        asyncio.run(db.execute("INSERT INTO jobs (name) VALUES (?)", ["nightly"]))
        rows = asyncio.run(db.fetch_all("SELECT * FROM jobs"))
        assert len(rows) == 1

    def test_notifications_push(self):
        from techforge_sdk.notifications import NotificationsSDK
        n = NotificationsSDK("test")
        notif = n.push("Test", "Message", "info")
        assert notif.title == "Test"
        assert len(n.pending()) == 1

    def test_notifications_mark_read(self):
        from techforge_sdk.notifications import NotificationsSDK
        n = NotificationsSDK("test")
        notif = n.push("T", "M")
        n.mark_read(notif.id)
        assert len(n.pending()) == 0


# ── hello_world module integration test ──────────────────────────────────────

class TestHelloWorldModule:

    def _load_module(self):
        hw_path = ROOT / "modules" / "installed" / "hello_world" / "backend"
        sys.path.insert(0, str(hw_path.parent.parent.parent))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "hello_world_backend",
            str(hw_path / "main.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_hello_world_loads(self):
        m = self._load_module()
        assert m.module is not None

    def test_hello_world_metadata(self):
        m = self._load_module()
        meta = m.module.metadata
        assert meta.id == "hello_world"
        assert meta.version == "1.0.0"

    def test_hello_world_lifecycle(self):
        m = self._load_module()
        asyncio.run(m.module.install())
        asyncio.run(m.module.enable())
        asyncio.run(m.module.disable())
        asyncio.run(m.module.upgrade("0.9.0"))

    def test_hello_world_health_check(self):
        m = self._load_module()
        result = asyncio.run(m.module.health_check())
        assert isinstance(result, HealthResult)
        assert result.is_healthy

    def test_hello_world_router_has_ping(self):
        m = self._load_module()
        routes = [r.path for r in m.router.routes]
        assert any("ping" in r for r in routes)

    def test_hello_world_validates_with_cli(self):
        hw = ROOT / "modules" / "installed" / "hello_world"
        report = ModuleCLIValidator.validate(hw)
        errors = [c for c in report.checks if not c.passed and c.level == "error"]
        assert not errors, f"hello_world validation errors: {[c.message for c in errors]}"
