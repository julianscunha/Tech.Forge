"""
Dependency Governance — modelo (Fase 8.1 §5/§8)
==================================================
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from packaging.specifiers import SpecifierSet
from packaging.version import Version


class TargetType(str, Enum):
    MODULE     = "module"
    CAPABILITY = "capability"


class DependencyStatus(str, Enum):
    SATISFIED             = "SATISFIED"
    MISSING               = "MISSING"
    INCOMPATIBLE_VERSION  = "INCOMPATIBLE_VERSION"
    DISABLED              = "DISABLED"
    CONFLICT              = "CONFLICT"
    CYCLIC                = "CYCLIC"
    OPTIONAL_UNAVAILABLE  = "OPTIONAL_UNAVAILABLE"


@dataclass
class Dependency:
    """
    One declared dependency edge (§5): target_type/target_id/version_range/
    required are declared by the manifest; status/resolution are filled in
    by the DependencyResolver, not at parse time.
    """
    target_type:   TargetType
    target_id:     str
    version_range: Optional[str] = None
    required:      bool = True
    status:        Optional[DependencyStatus] = None
    resolution:    Optional[str] = None   # human-readable provider/version that satisfied it

    def satisfies_version(self, version: str) -> bool:
        """True when *version* falls inside version_range (or no range declared)."""
        if not self.version_range:
            return True
        return Version(version) in SpecifierSet(self.version_range)
