"""
TechForge SDK — Python
======================
Official SDK for TechForge module backends.

Quick start:
    from techforge_sdk import sdk, create_sdk
    from techforge_sdk.contracts import ModuleContract, ModuleMetadata, HealthResult

    class MyModule(ModuleContract):
        @property
        def metadata(self) -> ModuleMetadata:
            return ModuleMetadata(
                id="my_module", name="My Module", version="1.0.0",
                category="Backup", vendor="ACME", author="Dev",
                description="Does things.",
            )

        async def install(self) -> None:
            sdk.logger.info("Installing my_module…")

        async def health_check(self):
            return HealthResult.ok()
        # ... implement remaining abstract methods

Services available via sdk.*:
    sdk.database      — isolated SQL access
    sdk.storage       — sandboxed file I/O
    sdk.logger        — structured, tagged logging
    sdk.settings      — persistent key-value config
    sdk.notifications — push UI notifications
"""
from techforge_sdk.core import TechForgeSDK, create_sdk
from techforge_sdk.contracts import ModuleContract, ModuleMetadata, HealthResult

# Default singleton — module_id will be "unknown" until replaced by
# create_sdk(module_id) inside the module's backend/main.py
sdk = TechForgeSDK(module_id="unknown")

__all__ = [
    "sdk",
    "create_sdk",
    "TechForgeSDK",
    "ModuleContract",
    "ModuleMetadata",
    "HealthResult",
]
