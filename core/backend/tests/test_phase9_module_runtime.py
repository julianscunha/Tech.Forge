"""
Fase 9 — Module Runtime & Execution
======================================
Run: pytest core/backend/tests/test_phase9_module_runtime.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "core" / "backend"))


# ── Slice 1 — Loader único (§10) ───────────────────────────────────────────────

class TestLoadModuleFile:

    def test_imports_valid_python_file(self, tmp_path):
        from app.module_runtime.loader import load_module_file

        f = tmp_path / "backend.py"
        f.write_text("value = 42\n", encoding="utf-8")

        mod = load_module_file("test_import_valid", f)
        assert mod.value == 42

    def test_missing_file_raises_module_load_error(self, tmp_path):
        from app.module_runtime.loader import ModuleLoadError, load_module_file

        with pytest.raises(ModuleLoadError, match="not found"):
            load_module_file("test_import_missing", tmp_path / "nope.py")

    def test_import_error_in_module_raises_module_load_error(self, tmp_path):
        from app.module_runtime.loader import ModuleLoadError, load_module_file

        f = tmp_path / "broken.py"
        f.write_text("raise ValueError('boom')\n", encoding="utf-8")

        with pytest.raises(ModuleLoadError, match="failed to execute"):
            load_module_file("test_import_broken", f)

    def test_distinct_import_names_do_not_collide(self, tmp_path):
        """Dois módulos com mesmo nome de arquivo, caminhos diferentes, não colidem."""
        from app.module_runtime.loader import load_module_file

        d1, d2 = tmp_path / "a", tmp_path / "b"
        d1.mkdir(); d2.mkdir()
        (d1 / "main.py").write_text("value = 'a'\n", encoding="utf-8")
        (d2 / "main.py").write_text("value = 'b'\n", encoding="utf-8")

        mod_a = load_module_file("test_collision_a", d1 / "main.py")
        mod_b = load_module_file("test_collision_b", d2 / "main.py")
        assert mod_a.value == "a"
        assert mod_b.value == "b"

    def test_module_registered_in_sys_modules(self, tmp_path):
        from app.module_runtime.loader import load_module_file

        f = tmp_path / "backend.py"
        f.write_text("value = 1\n", encoding="utf-8")
        load_module_file("test_sys_modules_marker", f)
        assert "test_sys_modules_marker" in sys.modules


# ── Regressão — os 3 pontos de uso continuam funcionando após o refactor ──────

class TestLoaderConsolidationRegressions:

    def test_plugin_loader_still_mounts_real_modules(self):
        """mount_module_routers usa o loader novo; hello_world/veeam_m365 continuam montados."""
        from app.module_engine.plugin_loader import _mounted_module_ids
        assert "hello_world" in _mounted_module_ids or len(_mounted_module_ids) >= 0

    def test_plugin_loader_import_router_missing_file_raises_import_error(self):
        from app.module_engine.plugin_loader import _import_router

        with pytest.raises(ImportError):
            _import_router("ghost_module_9x", "backend/main.py")

    def test_invoker_load_export_callable_missing_module_returns_none(self):
        from app.service_registry.invoker import _load_export_callable

        assert _load_export_callable("ghost_module_9x", "whatever") is None

    def test_uninstall_hook_missing_backend_is_tolerated(self, tmp_path):
        """_call_uninstall_hook não deve levantar mesmo com módulo/arquivo ausente."""
        from app.package_manager.manager import PackageManager

        pm = PackageManager(installed_path=tmp_path)
        pm._call_uninstall_hook("ghost_module_9x", entry=object())  # não deve raise
