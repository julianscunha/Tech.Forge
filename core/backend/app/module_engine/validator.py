"""
ModuleValidator
===============
Validates a module directory against the official TechForge module contract
(TechForge Architecture Specification §6) and checks platform compatibility.

The validator is intentionally separate from the ManifestParser so each
component has a single responsibility and can be tested in isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.module_engine.enums import ModuleStatus
from app.module_engine.manifest import ManifestError, ManifestParser, ParsedManifest

# ── Required directory structure per spec §6 ─────────────────────────────────

REQUIRED_SUBDIRS = ("backend", "frontend")
OPTIONAL_SUBDIRS = ("assets", "docs", "tests")
ALL_EXPECTED_SUBDIRS = REQUIRED_SUBDIRS + OPTIONAL_SUBDIRS


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    """
    The complete result of validating a module directory.

    is_valid    — True only when status is INSTALLED.
    status      — Final ModuleStatus.
    manifest    — Populated if the manifest was parseable, None otherwise.
    errors      — Human-readable descriptions of every problem found.
    warnings    — Non-fatal observations (missing optional dirs, etc.).
    """
    is_valid: bool
    status: ModuleStatus
    manifest: Optional[ParsedManifest] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ── Semver comparison helper ──────────────────────────────────────────────────

def _vt(v: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in v.split("."))
    except ValueError:
        return (0, 0, 0)


# ── Validator ─────────────────────────────────────────────────────────────────

class ModuleValidator:
    """
    Validates a module directory against the TechForge module contract.

    Usage:
        result = ModuleValidator.validate(
            module_path=Path("modules/installed/hello_world"),
            platform_version="1.0.0",
        )
    """

    @staticmethod
    def validate(module_path: Path, platform_version: str) -> ValidationResult:
        """
        Run all validation checks on *module_path*.

        Checks (in order):
        1. manifest.yaml exists and is parseable
        2. Required subdirectories are present
        3. Entry-point files declared in manifest exist
        4. Platform version is within declared compatibility range

        Args:
            module_path:       Absolute path to the module root directory.
            platform_version:  Running platform version string (e.g. "1.0.0").

        Returns:
            ValidationResult with status, errors, and warnings.
        """
        errors: list[str] = []
        warnings: list[str] = []
        manifest: Optional[ParsedManifest] = None

        # ── Step 1: parse manifest ────────────────────────────────────────────
        try:
            manifest = ManifestParser.parse(module_path)
        except ManifestError as exc:
            return ValidationResult(
                is_valid=False,
                status=ModuleStatus.INVALID,
                errors=[str(exc)],
            )

        # ── Step 2: directory structure ───────────────────────────────────────
        for subdir in REQUIRED_SUBDIRS:
            if not (module_path / subdir).is_dir():
                errors.append(
                    f"Required subdirectory '{subdir}/' is missing from module '{manifest.id}'."
                )

        for subdir in OPTIONAL_SUBDIRS:
            if not (module_path / subdir).is_dir():
                warnings.append(
                    f"Optional subdirectory '{subdir}/' is absent from module '{manifest.id}'."
                )

        # ── Step 3: entry-point existence ────────────────────────────────────
        backend_entry = module_path / manifest.entry_backend
        if not backend_entry.exists():
            errors.append(
                f"Backend entry point declared in manifest not found: {manifest.entry_backend}"
            )

        frontend_entry = module_path / manifest.entry_frontend
        if not frontend_entry.exists():
            errors.append(
                f"Frontend entry point declared in manifest not found: {manifest.entry_frontend}"
            )

        if errors:
            return ValidationResult(
                is_valid=False,
                status=ModuleStatus.INVALID,
                manifest=manifest,
                errors=errors,
                warnings=warnings,
            )

        # ── Step 4: platform compatibility ───────────────────────────────────
        pv = _vt(platform_version)
        min_v = _vt(manifest.platform_min_version)
        max_v = _vt(manifest.platform_max_version)

        if not (min_v <= pv <= max_v):
            errors.append(
                f"Platform version {platform_version} is outside the module's "
                f"declared compatibility range "
                f"[{manifest.platform_min_version}, {manifest.platform_max_version}]."
            )
            return ValidationResult(
                is_valid=False,
                status=ModuleStatus.INCOMPATIBLE,
                manifest=manifest,
                errors=errors,
                warnings=warnings,
            )

        # ── All checks passed ─────────────────────────────────────────────────
        return ValidationResult(
            is_valid=True,
            status=ModuleStatus.INSTALLED,
            manifest=manifest,
            errors=[],
            warnings=warnings,
        )
