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

    async def calculate_storage(
        self,
        users: int,
        mailbox_quota_gb: float,
        sharepoint_gb: float = 0.0,
        teams_gb: float = 0.0,
        retention_years: int = 1,
    ) -> dict:
        """
        Calcula uma estimativa simplificada de storage para backup M365.

        Esta é uma implementação de referência mínima — apenas para validar
        o contrato publicado em docs/contracts/api.yaml. Não substitui uma
        calculadora de sizing real de produção.
        """
        mailbox_total_gb = users * mailbox_quota_gb
        total_gb = mailbox_total_gb + sharepoint_gb + teams_gb

        # Fator de crescimento simplificado, cresce com o período de retenção
        growth_factor = round(1.0 + (retention_years * 0.1), 2)
        recommended_repo_gb = round(total_gb * growth_factor, 1)

        sdk.logger.info(
            "calculate_storage: users=%s total_gb=%.1f recommended=%.1f",
            users, total_gb, recommended_repo_gb,
        )

        return {
            "total_gb": round(total_gb, 1),
            "recommended_repo_gb": recommended_repo_gb,
            "growth_factor": growth_factor,
        }

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
