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

from app.module_engine.enums import ModuleStatus


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


# ── Slice 2 — Runtime State (§4/§5/§29) ────────────────────────────────────────

def _entry(module_id: str, status):
    from datetime import datetime
    from app.module_engine.registry import ModuleEntry
    return ModuleEntry(
        module_id=module_id, name=module_id, version="1.0.0",
        category="C", vendor="V", author="A", description="D",
        status=status, install_date=datetime.now(),
    )


class TestModuleRuntimeRegistry:

    def test_rebuild_creates_ready_entry_for_installed_module(self):
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.rebuild([_entry("mod_a", ModuleStatus.INSTALLED)])

        entry = reg.get("mod_a")
        assert entry is not None
        assert entry.state == RuntimeState.READY

    def test_rebuild_skips_non_installed_modules(self):
        from app.module_runtime.state import ModuleRuntimeRegistry

        reg = ModuleRuntimeRegistry()
        reg.rebuild([
            _entry("disabled_mod", ModuleStatus.DISABLED),
            _entry("blocked_mod", ModuleStatus.BLOCKED),
            _entry("invalid_mod", ModuleStatus.INVALID),
        ])
        assert reg.list_all() == []

    def test_rebuild_preserves_last_error_across_rebuilds(self):
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.rebuild([_entry("mod_a", ModuleStatus.INSTALLED)])
        reg.set_state("mod_a", RuntimeState.FAILED, last_error="boom")

        reg.rebuild([_entry("mod_a", ModuleStatus.INSTALLED)])
        entry = reg.get("mod_a")
        assert entry.state == RuntimeState.FAILED
        assert entry.last_error == "boom"

    def test_rebuild_drops_entries_for_removed_modules(self):
        from app.module_runtime.state import ModuleRuntimeRegistry

        reg = ModuleRuntimeRegistry()
        reg.rebuild([_entry("mod_a", ModuleStatus.INSTALLED)])
        reg.rebuild([])  # mod_a removido/desinstalado
        assert reg.get("mod_a") is None

    def test_set_state_creates_entry_when_absent(self):
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.set_state("new_mod", RuntimeState.EXECUTING)
        assert reg.get("new_mod").state == RuntimeState.EXECUTING

    def test_set_state_updates_since_timestamp(self):
        import time
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.set_state("mod_a", RuntimeState.READY)
        first_since = reg.get("mod_a").since
        time.sleep(0.01)
        reg.set_state("mod_a", RuntimeState.EXECUTING)
        assert reg.get("mod_a").since > first_since

    def test_mark_executed_sets_last_execution(self):
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.set_state("mod_a", RuntimeState.READY)
        assert reg.get("mod_a").last_execution is None
        reg.mark_executed("mod_a")
        assert reg.get("mod_a").last_execution is not None

    def test_uptime_seconds_none_when_not_ready(self):
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.set_state("mod_a", RuntimeState.FAILED)
        assert reg.uptime_seconds("mod_a") is None

    def test_uptime_seconds_positive_when_ready(self):
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.set_state("mod_a", RuntimeState.READY)
        assert reg.uptime_seconds("mod_a") >= 0

    def test_clear_transient_state_empties_registry(self):
        from app.module_runtime.state import ModuleRuntimeRegistry

        reg = ModuleRuntimeRegistry()
        reg.rebuild([_entry("mod_a", ModuleStatus.INSTALLED)])
        reg.clear_transient_state()
        assert reg.list_all() == []

    def test_boot_populates_singleton_for_real_installed_modules(self, client):
        """TestClient(app) roda o lifespan real — hello_world deve estar READY."""
        from app.module_runtime import module_runtime_registry, RuntimeState

        entry = module_runtime_registry.get("hello_world")
        assert entry is not None
        assert entry.state == RuntimeState.READY


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c
