"""
PackageInfo
===========
Represents the metadata extracted from a .mod archive or an installed module.
This is the data model the Marketplace UI and Package Manager work with.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.package_manager.catalog_source import CatalogSource
from app.package_manager.enums import CompatibilityLevel
from app.module_trust.trust import TrustLevel


@dataclass
class PackageInfo:
    """
    Full metadata about a package — either from a .mod file in the repository
    or from a module already installed.
    """
    # ── Identity ──────────────────────────────────────────────────────────────
    module_id:   str
    name:        str
    version:     str
    category:    str
    vendor:      str
    author:      str
    description: str

    # ── Compatibility ─────────────────────────────────────────────────────────
    platform_min_version: str = "0.0.0"
    platform_max_version: str = "999.999.999"
    compatibility: CompatibilityLevel = CompatibilityLevel.COMPATIBLE

    # ── Security (Phase 5 extension points) ───────────────────────────────────
    signature:  Optional[str] = None
    checksum:   Optional[str] = None
    publisher:  Optional[str] = None
    trust_level: TrustLevel   = TrustLevel.UNVERIFIED

    # ── Display ───────────────────────────────────────────────────────────────
    icon:  Optional[str] = None
    color: Optional[str] = None
    order: Optional[int] = None

    # ── Catalog source (Fase 11) ──────────────────────────────────────────────
    source: CatalogSource = CatalogSource.LOCAL
    source_url: Optional[str] = None     # URL of the catalog this package came from

    # ── Source ────────────────────────────────────────────────────────────────
    source_path: Optional[Path] = None    # path to the .mod file or installed dir

    # ── Installation state ────────────────────────────────────────────────────
    is_installed:      bool = False
    installed_version: Optional[str] = None
    install_date:      Optional[datetime] = None
    is_enabled:        Optional[bool] = None   # Fase 4: None = not installed

    # ── Links ─────────────────────────────────────────────────────────────────
    homepage:      Optional[str] = None
    documentation: Optional[str] = None

    @property
    def has_update(self) -> bool:
        """True when the repository has a newer version than what is installed."""
        if not self.is_installed or not self.installed_version:
            return False
        return _version_tuple(self.version) > _version_tuple(self.installed_version)

    @property
    def is_compatible(self) -> bool:
        return self.compatibility == CompatibilityLevel.COMPATIBLE

    @classmethod
    def from_manifest_dict(
        cls,
        raw: dict,
        source_path: Optional[Path] = None,
        platform_version: str = "1.0.0",
    ) -> "PackageInfo":
        from app.package_manager.compatibility import check_compatibility
        min_v = str(raw.get("platform_min_version", "0.0.0"))
        max_v = str(raw.get("platform_max_version", "999.999.999"))
        compat = check_compatibility(platform_version, min_v, max_v)
        return cls(
            module_id   = str(raw.get("id", "")).strip(),
            name        = str(raw.get("name", "")).strip(),
            version     = str(raw.get("version", "0.0.0")).strip(),
            category    = str(raw.get("category", "")).strip(),
            vendor      = str(raw.get("vendor", "")).strip(),
            author      = str(raw.get("author", "")).strip(),
            description = str(raw.get("description", "")).strip(),
            platform_min_version=min_v,
            platform_max_version=max_v,
            compatibility=compat,
            signature   = raw.get("signature"),
            checksum    = raw.get("checksum"),
            publisher   = raw.get("publisher"),
            trust_level = TrustLevel.UNVERIFIED,
            icon        = raw.get("icon"),
            color       = raw.get("color"),
            order       = int(raw["order"]) if raw.get("order") is not None else None,
            source_path = source_path,
            homepage    = raw.get("homepage"),
            documentation = raw.get("documentation"),
        )


def _version_tuple(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in v.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)
