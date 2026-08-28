"""
TechForge CLI — Package Builder (compat re-export)
====================================================
PackageBuilder moved to `app.package_manager.builder` (Core) in Fase 11,
because the Package Manager needs it at runtime (CustomCatalogProvider
builds a .mod on the fly from a remote git source) — the Core cannot
depend on the CLI package. This module stays as a thin re-export so
existing CLI imports (`from techforge_cli.packager.builder import
PackageBuilder`) keep working unchanged.
"""
from __future__ import annotations

from app.package_manager.builder import BuildResult, PackageBuilder

__all__ = ["BuildResult", "PackageBuilder"]
