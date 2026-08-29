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

import sys
from pathlib import Path

# `app` lives in core/backend/, a sibling of cli/ in the Tech.Forge repo.
# Importable by accident when the CLI is invoked with cwd=core/backend (a
# dev venv quirk), but not otherwise — e.g. a CI runner with a different
# cwd (see julianscunha/Tech.Forge.Modules CI, which installs this CLI from
# a checkout at an arbitrary path). Resolve it relative to this file instead
# of relying on cwd.
_CORE_BACKEND = Path(__file__).resolve().parents[3] / "core" / "backend"
if str(_CORE_BACKEND) not in sys.path:
    sys.path.insert(0, str(_CORE_BACKEND))

from app.package_manager.builder import BuildResult, PackageBuilder

__all__ = ["BuildResult", "PackageBuilder"]
