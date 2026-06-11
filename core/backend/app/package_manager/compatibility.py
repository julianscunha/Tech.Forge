"""
Compatibility Checker
======================
Determines whether a package is compatible with the running platform version.

Returns CompatibilityLevel:
  COMPATIBLE   — platform version is well within the declared range
  WARNING      — compatible but within one minor version of a boundary
  INCOMPATIBLE — platform version is outside the declared range
"""
from __future__ import annotations

from app.package_manager.enums import CompatibilityLevel


def _vt(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in str(v).split("."))
    except (ValueError, TypeError):
        return (0, 0, 0)


def check_compatibility(
    platform_version: str,
    min_version: str,
    max_version: str,
) -> CompatibilityLevel:
    """
    Check whether *platform_version* falls within [min_version, max_version].

    Args:
        platform_version: The running platform version string (e.g. "1.0.0").
        min_version:      Minimum supported platform version from manifest.
        max_version:      Maximum supported platform version from manifest.

    Returns:
        CompatibilityLevel enum value.
    """
    pv   = _vt(platform_version)
    minv = _vt(min_version)
    maxv = _vt(max_version)

    # Out of range → INCOMPATIBLE
    if not (minv <= pv <= maxv):
        return CompatibilityLevel.INCOMPATIBLE

    # Within one minor version of the max boundary → WARNING
    # Only applies when same major version as max
    if pv[0] == maxv[0] and pv != maxv and abs(pv[1] - maxv[1]) <= 1:
        return CompatibilityLevel.WARNING

    return CompatibilityLevel.COMPATIBLE


def format_compatibility(level: CompatibilityLevel) -> str:
    return {
        CompatibilityLevel.COMPATIBLE:   "Compatible",
        CompatibilityLevel.WARNING:      "Warning",
        CompatibilityLevel.INCOMPATIBLE: "Incompatible",
    }[level]
