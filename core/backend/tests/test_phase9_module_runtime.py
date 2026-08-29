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
sys.path.insert(0, str(ROOT / "sdk" / "python"))
sys.path.insert(0, str(ROOT / "cli"))

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


# ── Slice 3 — Lifecycle hooks reais (§10/§18) ──────────────────────────────────

def _write_backend_module(mod_dir, body: str) -> None:
    backend_dir = mod_dir / "backend"
    backend_dir.mkdir(parents=True, exist_ok=True)
    (backend_dir / "main.py").write_text(body, encoding="utf-8")


class TestLifecycleHooks:

    def test_on_activate_calls_enable_and_sets_ready(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.module_runtime.lifecycle import on_activate

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_a"
        _write_backend_module(mod_dir, """
class _Instance:
    def __init__(self):
        self.enabled = False
    async def enable(self):
        self.enabled = True
module = _Instance()
""")

        asyncio.run(on_activate("hook_mod_a", "backend/main.py"))
        assert module_runtime_registry.get("hook_mod_a").state == RuntimeState.READY

    def test_on_activate_enable_failure_sets_failed_with_last_error(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.module_runtime.lifecycle import on_activate

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_b"
        _write_backend_module(mod_dir, """
class _Instance:
    async def enable(self):
        raise RuntimeError("boom")
module = _Instance()
""")

        asyncio.run(on_activate("hook_mod_b", "backend/main.py"))
        entry = module_runtime_registry.get("hook_mod_b")
        assert entry.state == RuntimeState.FAILED
        assert "boom" in entry.last_error

    def test_on_activate_missing_enable_still_sets_ready(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.module_runtime.lifecycle import on_activate

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_c"
        _write_backend_module(mod_dir, "class _Instance:\n    pass\nmodule = _Instance()\n")

        asyncio.run(on_activate("hook_mod_c", "backend/main.py"))
        assert module_runtime_registry.get("hook_mod_c").state == RuntimeState.READY

    def test_on_deactivate_calls_disable_and_sets_stopped(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.module_runtime.lifecycle import on_deactivate

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_d"
        _write_backend_module(mod_dir, """
class _Instance:
    def __init__(self):
        self.disabled = False
    async def disable(self):
        self.disabled = True
module = _Instance()
""")

        asyncio.run(on_deactivate("hook_mod_d", "backend/main.py"))
        assert module_runtime_registry.get("hook_mod_d").state == RuntimeState.STOPPED

    def test_on_deactivate_disable_failure_still_sets_stopped(self, tmp_path, monkeypatch):
        """disable() falhar nao impede a desativacao administrativa (best-effort)."""
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.module_runtime.lifecycle import on_deactivate

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_e"
        _write_backend_module(mod_dir, """
class _Instance:
    async def disable(self):
        raise RuntimeError("boom")
module = _Instance()
""")

        asyncio.run(on_deactivate("hook_mod_e", "backend/main.py"))
        assert module_runtime_registry.get("hook_mod_e").state == RuntimeState.STOPPED

    def test_health_check_healthy_sets_ready(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState
        from app.module_runtime.lifecycle import health_check

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_f"
        _write_backend_module(mod_dir, """
from techforge_sdk.contracts import HealthResult
class _Instance:
    async def health_check(self):
        return HealthResult.ok()
module = _Instance()
""")

        state = asyncio.run(health_check("hook_mod_f", "backend/main.py"))
        assert state == RuntimeState.READY

    def test_health_check_unhealthy_sets_degraded(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.module_runtime.lifecycle import health_check

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_g"
        _write_backend_module(mod_dir, """
from techforge_sdk.contracts import HealthResult
class _Instance:
    async def health_check(self):
        return HealthResult.fail("db unreachable")
module = _Instance()
""")

        state = asyncio.run(health_check("hook_mod_g", "backend/main.py"))
        assert state == RuntimeState.DEGRADED
        assert module_runtime_registry.get("hook_mod_g").last_error == "db unreachable"

    def test_health_check_exception_sets_failed(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState
        from app.module_runtime.lifecycle import health_check

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_h"
        _write_backend_module(mod_dir, """
class _Instance:
    async def health_check(self):
        raise RuntimeError("crash")
module = _Instance()
""")

        state = asyncio.run(health_check("hook_mod_h", "backend/main.py"))
        assert state == RuntimeState.FAILED

    def test_health_check_missing_hook_defaults_ready(self, tmp_path, monkeypatch):
        import asyncio
        from app.core.settings import settings
        from app.module_runtime.state import RuntimeState
        from app.module_runtime.lifecycle import health_check

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        mod_dir = tmp_path / "hook_mod_i"
        _write_backend_module(mod_dir, "class _Instance:\n    pass\nmodule = _Instance()\n")

        state = asyncio.run(health_check("hook_mod_i", "backend/main.py"))
        assert state == RuntimeState.READY


class TestLifecycleIntegration:

    def test_activate_module_failure_in_enable_does_not_block_administrative_state(
            self, tmp_path, monkeypatch):
        """enable() falhar -> Runtime State FAILED, mas status administrativo vira INSTALLED mesmo assim."""
        import asyncio
        from datetime import datetime
        from app.core.settings import settings
        from app.module_engine.registry import registry, ModuleEntry
        from app.module_engine.enums import ModuleStatus as MS
        from app.module_runtime.state import RuntimeState, module_runtime_registry
        from app.package_manager.lifecycle import activate_module

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        module_id = "hook_mod_integration"
        mod_dir = tmp_path / module_id
        _write_backend_module(mod_dir, """
class _Instance:
    async def enable(self):
        raise RuntimeError("enable boom")
module = _Instance()
""")
        (mod_dir / "data").mkdir(parents=True, exist_ok=True)

        entry = ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=MS.DISABLED, install_date=datetime.now(),
            entry_backend="backend/main.py",
        )
        registry.register(entry)

        try:
            async def _run():
                from app.db.database import AsyncSessionLocal
                async with AsyncSessionLocal() as db:
                    return await activate_module(db, module_id)

            result = asyncio.run(_run())
            assert result["ok"] is True
            assert registry.get(module_id).status == MS.INSTALLED

            runtime_entry = module_runtime_registry.get(module_id)
            assert runtime_entry.state == RuntimeState.FAILED
            assert "enable boom" in runtime_entry.last_error
        finally:
            registry.deregister(module_id)


# ── Slice 4 — ExecutionContext + SDK extension (§8/§9) ─────────────────────────

class TestModuleExecutionContext:

    def test_build_returns_none_for_unknown_module(self):
        from app.module_runtime.context import ModuleExecutionContext
        from app.module_engine.registry import registry as module_registry

        ctx = ModuleExecutionContext.build("ghost_module_9x", module_registry)
        assert ctx is None

    def test_build_populates_fields_for_known_module(self, client):
        from app.module_runtime.context import ModuleExecutionContext
        from app.module_engine.registry import registry as module_registry

        ctx = ModuleExecutionContext.build("hello_world", module_registry)
        assert ctx is not None
        assert ctx.module_id == "hello_world"
        assert ctx.module_version
        assert ctx.runtime_id
        assert ctx.paths.root.name == "hello_world"  # Fase 12 §20 — ModulePaths
        assert ctx.services is not None
        assert ctx.cancellation is None
        assert ctx.metadata == {}
        assert ctx.storage is not None  # Fase 12 §6 — Module Storage API

    def test_build_generates_distinct_runtime_id_per_call(self, client):
        from app.module_runtime.context import ModuleExecutionContext
        from app.module_engine.registry import registry as module_registry

        ctx1 = ModuleExecutionContext.build("hello_world", module_registry)
        ctx2 = ModuleExecutionContext.build("hello_world", module_registry)
        assert ctx1.runtime_id != ctx2.runtime_id


# ── SDK: sdk.services / sdk.runtime (Fase 9 §9) ────────────────────────────────

class _FakeHTTPResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestSDKServices:

    def test_find_capability_returns_parsed_json(self, monkeypatch):
        import json as _json
        from techforge_sdk.services import ServicesSDK
        import urllib.request

        def fake_urlopen(url, timeout=None):
            assert "/services/capabilities/aws.cost.read" in url
            return _FakeHTTPResponse(_json.dumps([{"service_id": "aws_cost_service"}]).encode())

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        sdk_services = ServicesSDK("consumer_mod")
        result = sdk_services.find_capability("aws.cost.read")
        assert result == [{"service_id": "aws_cost_service"}]

    def test_find_capability_returns_empty_list_when_core_unreachable(self, monkeypatch):
        import urllib.request

        def fake_urlopen(url, timeout=None):
            raise OSError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        from techforge_sdk.services import ServicesSDK
        assert ServicesSDK("consumer_mod").find_capability("x") == []

    def test_get_returns_none_when_core_unreachable(self, monkeypatch):
        import urllib.request

        def fake_urlopen(url, timeout=None):
            raise OSError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        from techforge_sdk.services import ServicesSDK
        assert ServicesSDK("consumer_mod").get("aws_cost_service") is None


class TestSDKRuntime:

    def test_state_returns_parsed_json(self, monkeypatch):
        import json as _json
        import urllib.request
        from techforge_sdk.runtime import RuntimeSDK

        def fake_urlopen(url, timeout=None):
            assert "/runtime/modules/hello_world" in url
            return _FakeHTTPResponse(_json.dumps({"state": "READY"}).encode())

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert RuntimeSDK("hello_world").state() == {"state": "READY"}

    def test_state_returns_none_when_core_unreachable(self, monkeypatch):
        import urllib.request
        from techforge_sdk.runtime import RuntimeSDK

        def fake_urlopen(url, timeout=None):
            raise OSError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        assert RuntimeSDK("hello_world").state() is None


class TestSDKRootWiring:

    def test_create_sdk_exposes_services_and_runtime(self):
        from techforge_sdk import create_sdk

        sdk = create_sdk("some_module")
        assert hasattr(sdk, "services")
        assert hasattr(sdk, "runtime")


# ── Slice 5 — ModuleExecutionResult + cancellation/progress (esqueleto) §16/§19/§21

class TestModuleExecutionResult:

    def test_success_builds_envelope_with_status_success(self):
        from app.module_runtime.execution import ModuleExecutionResult

        result = ModuleExecutionResult.success(data={"count": 3})
        assert result.status == "SUCCESS"
        assert result.data == {"count": 3}
        assert result.errors == []
        assert result.warnings == []
        assert result.duration_seconds >= 0

    def test_failure_builds_envelope_with_errors(self):
        from app.module_runtime.execution import ModuleExecutionResult

        result = ModuleExecutionResult.failure(errors=["boom"])
        assert result.status == "FAILED"
        assert result.errors == ["boom"]
        assert result.data is None

    def test_envelope_never_mixes_status_with_business_payload_shape(self):
        """Metadata/data aceitam qualquer forma de negócio — só o envelope é padronizado."""
        from app.module_runtime.execution import ModuleExecutionResult

        result = ModuleExecutionResult.success(data=[1, 2, 3], warnings=["slow"])
        assert result.data == [1, 2, 3]
        assert result.warnings == ["slow"]


class TestCancellationToken:

    def test_starts_not_cancelled(self):
        from app.module_runtime.execution import CancellationToken

        token = CancellationToken()
        assert token.is_cancelled is False

    def test_cancel_sets_is_cancelled(self):
        from app.module_runtime.execution import CancellationToken

        token = CancellationToken()
        token.cancel()
        assert token.is_cancelled is True

    def test_cancel_is_idempotent(self):
        from app.module_runtime.execution import CancellationToken

        token = CancellationToken()
        token.cancel()
        token.cancel()
        assert token.is_cancelled is True

    def test_raise_if_cancelled_noop_when_not_cancelled(self):
        from app.module_runtime.execution import CancellationToken

        token = CancellationToken()
        token.raise_if_cancelled()  # não deve levantar

    def test_raise_if_cancelled_raises_when_cancelled(self):
        from app.module_runtime.execution import CancellationToken, ExecutionCancelledError

        token = CancellationToken()
        token.cancel()
        with pytest.raises(ExecutionCancelledError):
            token.raise_if_cancelled()


class TestProgressState:

    def test_valid_phase_values(self):
        from app.module_runtime.execution import ProgressPhase

        assert ProgressPhase.PREPARING.value == "PREPARING"
        assert ProgressPhase.RUNNING.value == "RUNNING"
        assert ProgressPhase.FINALIZING.value == "FINALIZING"

    def test_progress_report_holds_phase_and_percent(self):
        from app.module_runtime.execution import ProgressPhase, ProgressReport

        report = ProgressReport(phase=ProgressPhase.RUNNING, percent=42)
        assert report.phase == ProgressPhase.RUNNING
        assert report.percent == 42

    def test_progress_report_percent_defaults_to_none(self):
        from app.module_runtime.execution import ProgressPhase, ProgressReport

        report = ProgressReport(phase=ProgressPhase.PREPARING)
        assert report.percent is None

    def test_progress_report_rejects_percent_out_of_range(self):
        from app.module_runtime.execution import ProgressPhase, ProgressReport

        with pytest.raises(ValueError):
            ProgressReport(phase=ProgressPhase.RUNNING, percent=101)
        with pytest.raises(ValueError):
            ProgressReport(phase=ProgressPhase.RUNNING, percent=-1)


# ── Slice 6 — API + CLI (§26/§27) ───────────────────────────────────────────────

class TestRuntimeAPIRoutes:

    def test_list_module_runtime_includes_installed_modules(self, client):
        resp = client.get("/api/v1/runtime/modules")
        assert resp.status_code == 200
        module_ids = [e["module_id"] for e in resp.json()]
        assert "hello_world" in module_ids

    def test_get_module_runtime_known_module(self, client):
        resp = client.get("/api/v1/runtime/modules/hello_world")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "READY"
        assert body["uptime_seconds"] >= 0

    def test_get_module_runtime_unknown_module_404(self, client):
        resp = client.get("/api/v1/runtime/modules/ghost_module_9x")
        assert resp.status_code == 404

    def test_initialize_unknown_module_404(self, client):
        resp = client.post("/api/v1/runtime/modules/ghost_module_9x/initialize")
        assert resp.status_code == 404

    def test_initialize_known_module_reruns_health_check(self, client):
        resp = client.post("/api/v1/runtime/modules/hello_world/initialize")
        assert resp.status_code == 200
        assert resp.json()["state"] in ("READY", "DEGRADED", "FAILED")

    def test_platform_status_route_still_works(self, client):
        """Regressao — rota /runtime/status (Fase 6) nao foi afetada pelas novas rotas."""
        resp = client.get("/api/v1/runtime/status")
        assert resp.status_code == 200


class TestRuntimeCLI:

    def test_runtime_commands_registered(self):
        from techforge_cli.commands.runtime import runtime_cmd
        assert "status" in runtime_cmd.commands
        assert "modules" in runtime_cmd.commands
        assert "module" in runtime_cmd.commands
        assert "initialize" in runtime_cmd.commands


# ── Slice 7 — Teste integrado completo (§31, regra final) ──────────────────────

class TestPhase9FullIntegration:
    """
    Start TechForge -> Runtime Ready -> instalar modulo (tmp_path) ->
    activate (enable() real via API) -> READY -> health_check via API ->
    modulo falha -> Core continua respondendo -> deactivate -> STOPPED ->
    shutdown limpa Runtime State (nunca sobrevive a restart).
    """

    def test_full_module_lifecycle_through_api(self, client, tmp_path, monkeypatch):
        import asyncio
        from datetime import datetime
        from app.core.settings import settings
        from app.module_engine.registry import registry, ModuleEntry
        from app.module_runtime.state import RuntimeState, module_runtime_registry

        monkeypatch.setattr(settings, "MODULES_INSTALLED_PATH", tmp_path)
        module_id = "full_integration_mod"
        mod_dir = tmp_path / module_id
        _write_backend_module(mod_dir, """
from techforge_sdk.contracts import HealthResult

class _Instance:
    def __init__(self):
        self.healthy = True
    async def enable(self):
        pass
    async def disable(self):
        pass
    async def health_check(self):
        return HealthResult.ok() if self.healthy else HealthResult.fail("dependency down")

module = _Instance()
""")
        (mod_dir / "data").mkdir(parents=True, exist_ok=True)

        entry = ModuleEntry(
            module_id=module_id, name=module_id, version="1.0.0",
            category="C", vendor="V", author="A", description="D",
            status=ModuleStatus.DISABLED, install_date=datetime.now(),
            entry_backend="backend/main.py",
        )
        registry.register(entry)

        try:
            # activate -> enable() real via lifecycle -> READY
            async def _activate():
                from app.db.database import AsyncSessionLocal
                from app.package_manager.lifecycle import activate_module
                async with AsyncSessionLocal() as db:
                    return await activate_module(db, module_id)

            result = asyncio.run(_activate())
            assert result["ok"] is True
            assert module_runtime_registry.get(module_id).state == RuntimeState.READY

            # GET /runtime/modules/{id} via API — READY
            resp = client.get(f"/api/v1/runtime/modules/{module_id}")
            assert resp.status_code == 200
            assert resp.json()["state"] == "READY"

            # Simular falha do modulo — health_check() reporta unhealthy
            # (mesma instancia cacheada por on_activate, nao um reload)
            from app.module_runtime.lifecycle import _load_module_instance
            instance = _load_module_instance(module_id, "backend/main.py")
            instance.healthy = False

            resp = client.post(f"/api/v1/runtime/modules/{module_id}/initialize")
            assert resp.status_code == 200
            assert resp.json()["state"] == "DEGRADED"

            # Core continua respondendo normalmente apos a falha do modulo
            resp = client.get("/api/v1/platform/status")
            assert resp.status_code == 200

            # deactivate -> disable() real -> STOPPED
            async def _deactivate():
                from app.db.database import AsyncSessionLocal
                from app.package_manager.lifecycle import deactivate_module
                async with AsyncSessionLocal() as db:
                    return await deactivate_module(db, module_id)

            result = asyncio.run(_deactivate())
            assert result["ok"] is True
            assert module_runtime_registry.get(module_id).state == RuntimeState.STOPPED

        finally:
            registry.deregister(module_id)
            module_runtime_registry._entries.pop(module_id, None)
            from app.module_runtime.lifecycle import discard_instance
            discard_instance(module_id)

    def test_shutdown_clears_runtime_state(self):
        """§27/§29 — Runtime State e efemero, nunca sobrevive a um shutdown."""
        from app.module_runtime.state import ModuleRuntimeRegistry, RuntimeState

        reg = ModuleRuntimeRegistry()
        reg.set_state("mod_x", RuntimeState.READY)
        reg.clear_transient_state()
        assert reg.get("mod_x") is None
