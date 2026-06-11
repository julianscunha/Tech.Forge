"""
veeam_m365 — Backend Entry Point
===================================
Module    : veeam_m365
Name      : Veeam M365 Sizing
Category  : Backup
Vendor    : Veeam
Icon      : shield-check
Order     : 10

This is the backend stub for the Veeam M365 Sizing module.
Replace this with real sizing logic in a later phase.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "sdk" / "python"))

from fastapi import APIRouter
from techforge_sdk import create_sdk
from techforge_sdk.contracts import ModuleContract, ModuleMetadata, HealthResult

sdk = create_sdk("veeam_m365")

router = APIRouter(prefix="/modules/veeam_m365", tags=["veeam_m365"])


@router.get("/ping")
async def ping():
    sdk.logger.info("veeam_m365 ping called")
    return {"module": "veeam_m365", "status": "ok", "version": "1.0.0"}


class VeeamM365Module(ModuleContract):

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="veeam_m365",
            name="Veeam M365 Sizing",
            version="1.0.0",
            category="Backup",
            vendor="Veeam",
            author="TechForge Team",
            description="Sizing para Microsoft 365.",
            platform_min_version="1.0.0",
            platform_max_version="2.0.0",
        )

    async def install(self) -> None:
        sdk.logger.info("veeam_m365 install()")

    async def enable(self) -> None:
        sdk.logger.info("veeam_m365 enable()")

    async def disable(self) -> None:
        sdk.logger.info("veeam_m365 disable()")

    async def upgrade(self, from_version: str) -> None:
        sdk.logger.info("veeam_m365 upgrade() from %s", from_version)

    async def health_check(self) -> HealthResult:
        return HealthResult.ok("veeam_m365 is healthy.")

    async def uninstall(self) -> None:
        sdk.logger.info("veeam_m365 uninstall()")
        sdk.settings.reset()


module = VeeamM365Module()
