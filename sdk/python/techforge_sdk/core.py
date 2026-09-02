"""
TechForge SDK — Core
=====================
Assembles all SDK services into a single object accessed as sdk.*

Each module gets its own instance via create_sdk(module_id) so
services are scoped to that module's data directory and log prefix.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from techforge_sdk.database import DatabaseSDK
from techforge_sdk.logger import LoggerSDK
from techforge_sdk.notifications import NotificationsSDK
from techforge_sdk.runtime import RuntimeSDK
from techforge_sdk.services import ServicesSDK
from techforge_sdk.settings import SettingsSDK
from techforge_sdk.storage import StorageSDK


class TechForgeSDK:
    """
    Root SDK object.

    Module backends should call create_sdk(module_id) to get a properly
    scoped instance rather than importing the default singleton.
    """

    def __init__(
        self,
        module_id: str,
        data_dir: Optional[Path] = None,
    ) -> None:
        self._module_id = module_id

        self.database      = DatabaseSDK(module_id, data_dir)
        self.storage       = StorageSDK(module_id, data_dir)
        self.logger        = LoggerSDK(module_id)
        self.settings      = SettingsSDK(module_id, data_dir)
        self.notifications = NotificationsSDK(module_id)
        self.services      = ServicesSDK(module_id)
        self.runtime       = RuntimeSDK(module_id)

    def __repr__(self) -> str:
        return f"TechForgeSDK(module_id={self._module_id!r})"


def create_sdk(module_id: str, data_dir: Optional[Path] = None) -> TechForgeSDK:
    """
    Factory function — creates an SDK instance scoped to *module_id*.

    Call this at the top of your module's backend/main.py:

        from techforge_sdk import create_sdk
        sdk = create_sdk("my_module")

    This ensures all services (storage, settings, logger) use the correct
    namespaced paths and prefixes rather than the default "unknown" singleton.
    """
    return TechForgeSDK(module_id=module_id, data_dir=data_dir)
