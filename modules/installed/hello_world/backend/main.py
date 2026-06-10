"""
hello_world — Backend Entry Point
===================================
Reference module for the TechForge Phase 3 SDK and contracts.

Demonstrates:
  - create_sdk(module_id) for a scoped SDK instance
  - ModuleContract implementation with all lifecycle hooks
  - FastAPI router exported for Plugin Loader dynamic mounting
"""
import sys
from pathlib import Path

# Allow running from the module directory directly during development
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "sdk" / "python"))

from fastapi import APIRouter
from techforge_sdk import create_sdk
from techforge_sdk.contracts import ModuleContract, ModuleMetadata, HealthResult

# ── SDK scoped to this module ─────────────────────────────────────────────────
sdk = create_sdk("hello_world")

# ── Router — mounted by Plugin Loader at /api/v1/modules/hello_world ──────────
router = APIRouter(prefix="/modules/hello_world", tags=["hello_world"])


@router.get("/ping")
async def ping():
    sdk.logger.info("ping called")
    return {"module": "hello_world", "status": "ok", "version": "1.0.0"}


@router.get("/info")
async def info():
    return {
        "module_id":   "hello_world",
        "name":        "Hello World",
        "category":    "Examples",
        "vendor":      "TechForge",
        "sdk_version": "1.0.0",
        "description": "Reference module — architecture validation only.",
    }


# ── ModuleContract implementation ─────────────────────────────────────────────

class HelloWorldModule(ModuleContract):

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="hello_world",
            name="Hello World",
            version="1.0.0",
            category="Examples",
            vendor="TechForge",
            author="TechForge Team",
            description="Reference module — architecture validation only.",
            platform_min_version="1.0.0",
            platform_max_version="999.999.999",
        )

    async def install(self) -> None:
        sdk.logger.info("hello_world install() called")
        sdk.settings.set("installed", True)
        sdk.settings.set("install_count",
                         sdk.settings.get("install_count", 0) + 1)

    async def enable(self) -> None:
        sdk.logger.info("hello_world enable() called")

    async def disable(self) -> None:
        sdk.logger.info("hello_world disable() called")

    async def upgrade(self, from_version: str) -> None:
        sdk.logger.info("hello_world upgrade() from %s", from_version)

    async def health_check(self) -> HealthResult:
        return HealthResult.ok(
            "hello_world is healthy",
            install_count=sdk.settings.get("install_count", 0),
        )

    async def uninstall(self) -> None:
        sdk.logger.info("hello_world uninstall() called")
        sdk.settings.reset()


module = HelloWorldModule()
