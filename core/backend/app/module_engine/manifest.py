"""
ManifestParser
==============
Reads a module's manifest.yaml file, validates all required fields, checks
semantic correctness, and returns a structured ParsedManifest dataclass.

Raises ManifestError with a human-readable message on any violation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# ── Exceptions ────────────────────────────────────────────────────────────────

class ManifestError(Exception):
    """Raised when a manifest.yaml is missing, malformed, or invalid."""


# ── Parsed Manifest dataclass ─────────────────────────────────────────────────

@dataclass
class ParsedManifest:
    """
    Strongly-typed representation of a validated manifest.yaml.
    All fields mirror the spec in TechForge Architecture Specification §7.
    """
    # Required fields
    id: str
    name: str
    version: str
    category: str
    vendor: str
    author: str
    description: str
    entry_backend: str
    entry_frontend: str

    # Version constraints (required by spec; default to open range if absent)
    platform_min_version: str = "0.0.0"
    platform_max_version: str = "999.999.999"

    # Optional fields
    homepage: Optional[str] = None
    documentation: Optional[str] = None

    # Security fields — populated in Phase 5
    signature: Optional[str] = None
    checksum: Optional[str] = None

    # Raw parsed content preserved for Developer Mode display
    raw: dict = field(default_factory=dict, repr=False)


# ── Semver helper ─────────────────────────────────────────────────────────────

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _assert_semver(value: str, field_name: str) -> None:
    if not _SEMVER_RE.match(value):
        raise ManifestError(
            f"Field '{field_name}' must follow semver format (X.Y.Z), got: {value!r}"
        )


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


# ── Parser ────────────────────────────────────────────────────────────────────

REQUIRED_FIELDS = (
    "id", "name", "version", "category", "vendor",
    "author", "description", "entry_backend", "entry_frontend",
)


class ManifestParser:
    """
    Stateless parser for module manifest.yaml files.

    Usage:
        manifest = ManifestParser.parse(Path("modules/installed/hello_world"))
    """

    @staticmethod
    def parse(module_path: Path) -> ParsedManifest:
        """
        Locate, load, and validate the manifest.yaml inside *module_path*.

        Args:
            module_path: Absolute or relative path to the module root directory.

        Returns:
            ParsedManifest instance with all fields populated.

        Raises:
            ManifestError: on any structural or semantic violation.
        """
        manifest_file = module_path / "manifest.yaml"

        # ── File existence ────────────────────────────────────────────────────
        if not manifest_file.exists():
            raise ManifestError(
                f"manifest.yaml not found in module directory: {module_path}"
            )

        # ── YAML parse ────────────────────────────────────────────────────────
        try:
            raw: dict = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ManifestError(f"manifest.yaml is not valid YAML: {exc}") from exc

        if not isinstance(raw, dict):
            raise ManifestError("manifest.yaml must be a YAML mapping at the top level.")

        # ── Required fields presence ──────────────────────────────────────────
        missing = [f for f in REQUIRED_FIELDS if not raw.get(f)]
        if missing:
            raise ManifestError(
                f"manifest.yaml is missing required fields: {', '.join(missing)}"
            )

        # ── Semver validation ─────────────────────────────────────────────────
        _assert_semver(str(raw["version"]), "version")

        platform_min = str(raw.get("platform_min_version", "0.0.0"))
        platform_max = str(raw.get("platform_max_version", "999.999.999"))
        _assert_semver(platform_min, "platform_min_version")
        _assert_semver(platform_max, "platform_max_version")

        if _version_tuple(platform_min) > _version_tuple(platform_max):
            raise ManifestError(
                f"platform_min_version ({platform_min}) must be ≤ platform_max_version ({platform_max})"
            )

        # ── id format ────────────────────────────────────────────────────────
        module_id = str(raw["id"]).strip()
        if not re.match(r"^[a-z][a-z0-9_]{1,63}$", module_id):
            raise ManifestError(
                f"Module id must be lowercase snake_case, 2-64 chars, got: {module_id!r}"
            )

        return ParsedManifest(
            id=module_id,
            name=str(raw["name"]).strip(),
            version=str(raw["version"]).strip(),
            category=str(raw["category"]).strip(),
            vendor=str(raw["vendor"]).strip(),
            author=str(raw["author"]).strip(),
            description=str(raw["description"]).strip(),
            entry_backend=str(raw["entry_backend"]).strip(),
            entry_frontend=str(raw["entry_frontend"]).strip(),
            platform_min_version=platform_min,
            platform_max_version=platform_max,
            homepage=raw.get("homepage"),
            documentation=raw.get("documentation"),
            signature=raw.get("signature"),
            checksum=raw.get("checksum"),
            raw=raw,
        )
