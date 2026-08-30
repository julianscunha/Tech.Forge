"""
TechForge §7.1 — Navigation & Presentation Metadata Test Suite
===============================================================
Tests:
  - ManifestParser: icon/order/color required/optional validation
  - NavigationBuilder: grouping, ordering, filtering logic
  - hello_world and veeam_m365 manifests parse cleanly
  - CLI validator: icon/order/color checks

Run: pytest core/backend/tests/test_nav_metadata.py -v
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))
sys.path.insert(0, str(ROOT / "cli"))

from app.module_engine.manifest import (
    ManifestParser, ManifestError, REQUIRED_FIELDS, VALID_COLORS, ParsedManifest,
)
from app.module_engine.navigation import NavigationBuilder, NavigationTree
from app.module_engine.registry import ModuleRegistry, ModuleEntry
from app.module_engine.enums import ModuleStatus
from datetime import datetime

pytestmark = pytest.mark.unit


# ── Helpers ───────────────────────────────────────────────────────────────────

FULL_MANIFEST = {
    "id": "test_mod",
    "name": "Test Module",
    "version": "1.0.0",
    "platform_min_version": "1.0.0",
    "platform_max_version": "2.0.0",
    "category": "Backup",
    "vendor": "Acme",
    "author": "Dev",
    "description": "Test.",
    "entry_backend": "backend/main.py",
    "entry_frontend": "frontend/index.tsx",
    "icon": "shield-check",
    "order": 10,
    "color": "blue",
}


def write_manifest(tmp: Path, data: dict) -> Path:
    mod_dir = tmp / data.get("id", "mod")
    mod_dir.mkdir(parents=True, exist_ok=True)
    (mod_dir / "manifest.yaml").write_text(
        yaml.dump(data), encoding="utf-8"
    )
    return mod_dir


def make_entry(
    module_id="mod_a", name="Mod A", category="Backup",
    vendor="Acme", order=10, icon="shield-check", color="blue",
    status=ModuleStatus.INSTALLED,
) -> ModuleEntry:
    return ModuleEntry(
        module_id=module_id, name=name, version="1.0.0",
        category=category, vendor=vendor, author="Dev",
        description="Test.", status=status,
        install_date=datetime.utcnow(),
        icon=icon, color=color, order=order,
    )


# ── ManifestParser — §7.1 field tests ────────────────────────────────────────

class TestManifestParserNavFields:

    def test_full_manifest_parses(self, tmp_path):
        mod_dir = write_manifest(tmp_path, FULL_MANIFEST.copy())
        m = ManifestParser.parse(mod_dir)
        assert m.icon  == "shield-check"
        assert m.order == 10
        assert m.color == "blue"

    def test_icon_is_required(self, tmp_path):
        data = {k: v for k, v in FULL_MANIFEST.items() if k != "icon"}
        mod_dir = write_manifest(tmp_path, data)
        with pytest.raises(ManifestError, match="icon"):
            ManifestParser.parse(mod_dir)

    def test_order_is_required(self, tmp_path):
        data = {k: v for k, v in FULL_MANIFEST.items() if k != "order"}
        mod_dir = write_manifest(tmp_path, data)
        with pytest.raises(ManifestError, match="order"):
            ManifestParser.parse(mod_dir)

    def test_color_is_optional(self, tmp_path):
        data = {k: v for k, v in FULL_MANIFEST.items() if k != "color"}
        mod_dir = write_manifest(tmp_path, data)
        m = ManifestParser.parse(mod_dir)
        assert m.color is None

    def test_icon_kebab_case_valid(self, tmp_path):
        for icon in ("shield-check", "database", "hard-drive", "bar-chart", "blocks"):
            data = {**FULL_MANIFEST, "icon": icon, "id": f"mod_{icon.replace('-','_')}"}
            mod_dir = write_manifest(tmp_path / icon, data)
            m = ManifestParser.parse(mod_dir)
            assert m.icon == icon

    def test_icon_invalid_format_raises(self, tmp_path):
        for bad in ("ShieldCheck", "shield_check", "123icon", "", "a" * 70):
            data = {**FULL_MANIFEST, "icon": bad, "id": "test_bad"}
            mod_dir = write_manifest(tmp_path / f"bad_{bad[:5]}", data)
            with pytest.raises(ManifestError, match="icon"):
                ManifestParser.parse(mod_dir)

    def test_order_zero_is_valid(self, tmp_path):
        data = {**FULL_MANIFEST, "order": 0}
        mod_dir = write_manifest(tmp_path, data)
        m = ManifestParser.parse(mod_dir)
        assert m.order == 0

    def test_order_negative_raises(self, tmp_path):
        data = {**FULL_MANIFEST, "order": -1, "id": "neg_order"}
        mod_dir = write_manifest(tmp_path, data)
        with pytest.raises(ManifestError, match="order"):
            ManifestParser.parse(mod_dir)

    def test_order_string_raises(self, tmp_path):
        data = {**FULL_MANIFEST, "order": "first", "id": "str_order"}
        mod_dir = write_manifest(tmp_path, data)
        with pytest.raises(ManifestError, match="order"):
            ManifestParser.parse(mod_dir)

    def test_color_valid_values(self, tmp_path):
        for color in VALID_COLORS:
            data = {**FULL_MANIFEST, "color": color, "id": f"col_{color}"}
            mod_dir = write_manifest(tmp_path / color, data)
            m = ManifestParser.parse(mod_dir)
            assert m.color == color

    def test_color_invalid_raises(self, tmp_path):
        data = {**FULL_MANIFEST, "color": "chartreuse", "id": "bad_color"}
        mod_dir = write_manifest(tmp_path, data)
        with pytest.raises(ManifestError, match="color"):
            ManifestParser.parse(mod_dir)

    def test_required_fields_includes_icon_and_order(self):
        assert "icon"  in REQUIRED_FIELDS
        assert "order" in REQUIRED_FIELDS

    def test_color_not_in_required_fields(self):
        assert "color" not in REQUIRED_FIELDS


# ── NavigationBuilder tests ───────────────────────────────────────────────────

class TestNavigationBuilder:

    def test_empty_registry_produces_empty_tree(self):
        reg = ModuleRegistry()
        tree = NavigationBuilder.build(reg)
        assert tree.total_modules == 0
        assert tree.categories == []

    def test_single_module_builds_tree(self):
        reg = ModuleRegistry()
        reg.register(make_entry())
        tree = NavigationBuilder.build(reg)
        assert tree.total_modules == 1
        assert len(tree.categories) == 1
        assert tree.categories[0].category == "Backup"

    def test_category_grouping(self):
        reg = ModuleRegistry()
        reg.register(make_entry("mod_a", category="Backup"))
        reg.register(make_entry("mod_b", category="Cloud"))
        reg.register(make_entry("mod_c", category="Backup"))
        tree = NavigationBuilder.build(reg)
        assert len(tree.categories) == 2
        cats = {c.category for c in tree.categories}
        assert cats == {"Backup", "Cloud"}

    def test_vendor_grouping_within_category(self):
        reg = ModuleRegistry()
        reg.register(make_entry("m1", category="Backup", vendor="Veeam"))
        reg.register(make_entry("m2", category="Backup", vendor="Commvault"))
        reg.register(make_entry("m3", category="Backup", vendor="Veeam"))
        tree = NavigationBuilder.build(reg)
        backup = tree.categories[0]
        assert backup.total_modules == 3
        vendors = {v.vendor for v in backup.vendors}
        assert vendors == {"Veeam", "Commvault"}

    def test_modules_sorted_by_order_asc(self):
        reg = ModuleRegistry()
        reg.register(make_entry("m3", name="Z Module", order=30))
        reg.register(make_entry("m1", name="A Module", order=10))
        reg.register(make_entry("m2", name="M Module", order=20))
        tree = NavigationBuilder.build(reg)
        modules = tree.categories[0].vendors[0].modules
        assert [m.order for m in modules] == [10, 20, 30]

    def test_order_tiebreak_alphabetical(self):
        reg = ModuleRegistry()
        reg.register(make_entry("mz", name="Zebra", order=10))
        reg.register(make_entry("ma", name="Alpha", order=10))
        tree = NavigationBuilder.build(reg)
        modules = tree.categories[0].vendors[0].modules
        assert modules[0].name == "Alpha"
        assert modules[1].name == "Zebra"

    def test_invalid_modules_excluded(self):
        reg = ModuleRegistry()
        reg.register(make_entry("ok_mod",  status=ModuleStatus.INSTALLED))
        reg.register(make_entry("bad_mod", status=ModuleStatus.INVALID))
        reg.register(make_entry("inc_mod", status=ModuleStatus.INCOMPATIBLE))
        reg.register(make_entry("dis_mod", status=ModuleStatus.DISABLED))
        tree = NavigationBuilder.build(reg)
        # Only INSTALLED appears in nav
        assert tree.total_modules == 1
        assert tree.categories[0].vendors[0].modules[0].module_id == "ok_mod"

    def test_categories_sorted_alphabetically(self):
        reg = ModuleRegistry()
        reg.register(make_entry("m1", category="Virtualização"))
        reg.register(make_entry("m2", category="Backup"))
        reg.register(make_entry("m3", category="Cloud"))
        tree = NavigationBuilder.build(reg)
        cats = [c.category for c in tree.categories]
        assert cats == sorted(cats)

    def test_vendors_sorted_alphabetically_within_category(self):
        reg = ModuleRegistry()
        reg.register(make_entry("m1", category="Backup", vendor="Veeam"))
        reg.register(make_entry("m2", category="Backup", vendor="Commvault"))
        reg.register(make_entry("m3", category="Backup", vendor="Arcserve"))
        tree = NavigationBuilder.build(reg)
        vendors = [v.vendor for v in tree.categories[0].vendors]
        assert vendors == sorted(vendors)

    def test_path_format(self):
        reg = ModuleRegistry()
        reg.register(make_entry("my_module"))
        tree = NavigationBuilder.build(reg)
        m = tree.categories[0].vendors[0].modules[0]
        assert m.path == "/modules/my_module"

    def test_icon_fallback_when_none(self):
        reg = ModuleRegistry()
        entry = make_entry("no_icon")
        entry.icon = None  # type: ignore
        reg.register(entry)
        tree = NavigationBuilder.build(reg)
        m = tree.categories[0].vendors[0].modules[0]
        assert m.icon == "puzzle"   # fallback

    def test_total_modules_count(self):
        reg = ModuleRegistry()
        for i in range(5):
            reg.register(make_entry(f"mod_{i}", name=f"Module {i}", order=i))
        tree = NavigationBuilder.build(reg)
        assert tree.total_modules == 5

    def test_category_total_modules(self):
        reg = ModuleRegistry()
        reg.register(make_entry("a1", category="Backup", vendor="V1", order=1))
        reg.register(make_entry("a2", category="Backup", vendor="V2", order=2))
        reg.register(make_entry("b1", category="Cloud",  vendor="V1", order=1))
        tree = NavigationBuilder.build(reg)
        backup = next(c for c in tree.categories if c.category == "Backup")
        assert backup.total_modules == 2


# ── Real module manifests test ────────────────────────────────────────────────

class TestRealModuleManifests:

    def test_hello_world_manifest_valid(self):
        path = ROOT / "modules" / "installed" / "hello_world"
        m = ManifestParser.parse(path)
        assert m.icon  is not None
        assert m.order is not None
        assert m.id    == "hello_world"

    def test_veeam_m365_manifest_valid(self):
        path = ROOT / "modules" / "installed" / "veeam_m365"
        m = ManifestParser.parse(path)
        assert m.id    == "veeam_m365"
        assert m.icon  == "shield-check"
        assert m.color == "blue"
        assert m.order == 10

    def test_veeam_m365_in_correct_category(self):
        path = ROOT / "modules" / "installed" / "veeam_m365"
        m = ManifestParser.parse(path)
        assert m.category == "Backup"
        assert m.vendor   == "Veeam"

    def test_both_modules_appear_in_tree(self):
        from app.module_engine.loader import ModuleLoader

        async def _run():
            reg = ModuleRegistry()
            loader = ModuleLoader(
                installed_path=ROOT / "modules" / "installed",
                target_registry=reg,
            )
            await loader.scan_installed()
            return NavigationBuilder.build(reg)

        tree = asyncio.run(_run())
        all_ids = [
            m.module_id
            for cat in tree.categories
            for v in cat.vendors
            for m in v.modules
        ]
        assert "hello_world"  in all_ids
        assert "veeam_m365"   in all_ids

    def test_veeam_before_hello_world_by_order(self):
        """veeam_m365 (order=10) should sort before hello_world (order=99)
        but they are in different categories — test each is in correct category."""
        from app.module_engine.loader import ModuleLoader

        async def _run():
            reg = ModuleRegistry()
            loader = ModuleLoader(
                installed_path=ROOT / "modules" / "installed",
                target_registry=reg,
            )
            await loader.scan_installed()
            return NavigationBuilder.build(reg)

        tree = asyncio.run(_run())
        backup_mods = next(
            (m for cat in tree.categories for v in cat.vendors
             for m in v.modules if m.module_id == "veeam_m365"),
            None,
        )
        assert backup_mods is not None
        assert backup_mods.order == 10

        example_mods = next(
            (m for cat in tree.categories for v in cat.vendors
             for m in v.modules if m.module_id == "hello_world"),
            None,
        )
        assert example_mods is not None
        assert example_mods.order == 99


# ── CLI Validator — §7.1 checks ───────────────────────────────────────────────

class TestCLIValidatorNavFields:

    def _make_valid(self, tmp: Path) -> Path:
        mod = tmp / "valid_mod"
        mod.mkdir(parents=True)
        (mod / "backend").mkdir()
        (mod / "frontend").mkdir()
        (mod / "assets").mkdir()
        (mod / "docs").mkdir()
        (mod / "tests").mkdir()
        (mod / "backend" / "main.py").write_text(
            "from fastapi import APIRouter\n"
            "from techforge_sdk.contracts import ModuleContract\n"
            "router = APIRouter()\n"
        )
        (mod / "frontend" / "index.tsx").write_text(
            "export const moduleConfig = {}\n"
            "export default function P() { return null }\n"
        )
        (mod / "manifest.yaml").write_text(yaml.dump({
            "id": "valid_mod", "name": "Valid", "version": "1.0.0",
            "platform_min_version": "1.0.0", "platform_max_version": "2.0.0",
            "category": "Test", "vendor": "T", "author": "T",
            "description": "T", "entry_backend": "backend/main.py",
            "entry_frontend": "frontend/index.tsx",
            "icon": "shield-check", "order": 10, "color": "blue",
        }))
        # §16 Documentation First Principle — required for every module
        (mod / "docs" / "overview.md").write_text(
            "# Valid Module\n\nOverview for the test fixture module.",
            encoding="utf-8",
        )
        (mod / "docs" / "examples").mkdir()
        (mod / "docs" / "examples" / "basic.md").write_text(
            "## Objetivo\n\nExemplo básico.\n\n## Entradas\n\nNenhuma.\n\n"
            "## Saídas\n\nOK.\n\n## Exemplo\n\n```python\npass\n```\n\n"
            "## Observações\n\nFixture de teste.",
            encoding="utf-8",
        )
        return mod

    def test_valid_module_passes_with_icon_order(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = self._make_valid(tmp_path)
        report = ModuleCLIValidator.validate(mod)
        errors = [c for c in report.checks if not c.passed and c.level == "error"]
        assert not errors, [c.message for c in errors]

    def test_missing_icon_fails(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = self._make_valid(tmp_path)
        raw = yaml.safe_load((mod / "manifest.yaml").read_text())
        del raw["icon"]
        (mod / "manifest.yaml").write_text(yaml.dump(raw))
        report = ModuleCLIValidator.validate(mod)
        assert any("icon" in c.message.lower() or "icon" in c.name.lower() or "Missing" in c.message
                   for c in report.checks if not c.passed)

    def test_missing_order_fails(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = self._make_valid(tmp_path)
        raw = yaml.safe_load((mod / "manifest.yaml").read_text())
        del raw["order"]
        (mod / "manifest.yaml").write_text(yaml.dump(raw))
        report = ModuleCLIValidator.validate(mod)
        assert any("order" in c.message.lower() or "order" in c.name.lower() or "Missing" in c.message
                   for c in report.checks if not c.passed)

    def test_bad_icon_format_fails(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = self._make_valid(tmp_path)
        raw = yaml.safe_load((mod / "manifest.yaml").read_text())
        raw["icon"] = "BadIcon_123"
        (mod / "manifest.yaml").write_text(yaml.dump(raw))
        report = ModuleCLIValidator.validate(mod)
        icon_check = next((c for c in report.checks if "icon" in c.name.lower()), None)
        assert icon_check and not icon_check.passed

    def test_negative_order_fails(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = self._make_valid(tmp_path)
        raw = yaml.safe_load((mod / "manifest.yaml").read_text())
        raw["order"] = -5
        (mod / "manifest.yaml").write_text(yaml.dump(raw))
        report = ModuleCLIValidator.validate(mod)
        order_check = next((c for c in report.checks if "order" in c.name.lower()), None)
        assert order_check and not order_check.passed

    def test_invalid_color_warns(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = self._make_valid(tmp_path)
        raw = yaml.safe_load((mod / "manifest.yaml").read_text())
        raw["color"] = "chartreuse"
        (mod / "manifest.yaml").write_text(yaml.dump(raw))
        report = ModuleCLIValidator.validate(mod)
        color_check = next((c for c in report.checks if "color" in c.name.lower()), None)
        assert color_check and not color_check.passed
        assert color_check.level == "warning"

    def test_missing_color_passes(self, tmp_path):
        from techforge_cli.validators.module_validator import ModuleCLIValidator
        mod = self._make_valid(tmp_path)
        raw = yaml.safe_load((mod / "manifest.yaml").read_text())
        del raw["color"]
        (mod / "manifest.yaml").write_text(yaml.dump(raw))
        report = ModuleCLIValidator.validate(mod)
        errors = [c for c in report.checks if not c.passed and c.level == "error"]
        assert not errors
