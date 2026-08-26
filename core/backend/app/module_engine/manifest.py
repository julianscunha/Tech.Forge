"""
ManifestParser
==============
Reads a module's manifest.yaml file, validates all required fields, checks
semantic correctness, and returns a structured ParsedManifest dataclass.

Raises ManifestError with a human-readable message on any violation.

§7.1 — Navigation & Presentation fields (icon, order) are REQUIRED.
       color is optional but validated when present.
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
    All fields mirror TechForge Architecture Specification §7 and §7.1.
    """
    # ── Required identity fields ──────────────────────────────────────────────
    id: str
    name: str
    version: str
    category: str
    vendor: str
    author: str
    description: str
    entry_backend: str
    entry_frontend: str

    # ── Required navigation/presentation fields (§7.1) ────────────────────────
    icon: str          # lucide-react icon name — e.g. "shield-check", "database"
    order: int         # display order within category/vendor group (lower = first)

    # ── Version constraints ───────────────────────────────────────────────────
    platform_min_version: str = "0.0.0"
    platform_max_version: str = "999.999.999"

    # ── Optional presentation field (§7.1) ────────────────────────────────────
    color: Optional[str] = None   # accent color hint — "blue", "green", "red", etc.

    # ── Optional metadata ─────────────────────────────────────────────────────
    homepage: Optional[str] = None
    documentation: Optional[str] = None

    # ── Documentation versioning (Fase 5 §17) ─────────────────────────────────
    documentation_version: Optional[str] = None
    documentation_applies_to: Optional[dict] = None

    # ── Security fields — Phase 5 ─────────────────────────────────────────────
    signature: Optional[str] = None
    checksum: Optional[str] = None

    # ── Origin (Fase 4 §4): catalog | local | development ────────────────────
    source_type: str = "local"
    source_location: Optional[str] = None

    # ── Raw YAML — preserved for Developer Mode ─────────────────────────────
    raw: dict = field(default_factory=dict, repr=False)


# ── Validation helpers ────────────────────────────────────────────────────────

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Lucide icon names are kebab-case letters/digits/hyphens, 2–64 chars
_ICON_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")

# Valid color accent names accepted by the design system
VALID_COLORS = {
    "blue", "green", "red", "yellow", "orange",
    "purple", "pink", "cyan", "teal", "indigo", "gray",
}


def _assert_semver(value: str, field_name: str) -> None:
    if not _SEMVER_RE.match(value):
        raise ManifestError(
            f"Field '{field_name}' must follow semver format (X.Y.Z), got: {value!r}"
        )


def _parse_documentation_versioning(raw: dict) -> dict:
    """Parse optional documentation.version/applies_to block (Fase 5 §17)."""
    doc = raw.get("documentation")
    if not isinstance(doc, dict):
        return {"documentation_version": None, "documentation_applies_to": None}
    version = doc.get("version")
    if version is not None:
        _assert_semver(str(version), "documentation.version")
    applies = doc.get("applies_to") or None
    return {
        "documentation_version": str(version) if version else None,
        "documentation_applies_to": applies,
    }


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


# ── Required fields ───────────────────────────────────────────────────────────
# icon and order added per §7.1 — now mandatory.

REQUIRED_FIELDS = (
    "id", "name", "version", "category", "vendor",
    "author", "description", "entry_backend", "entry_frontend",
    "icon", "order",
)


# ── Parser ────────────────────────────────────────────────────────────────────

class ManifestParser:
    """
    Stateless parser for module manifest.yaml files.

    Usage:
        manifest = ManifestParser.parse(Path("modules/installed/veeam_m365"))
    """

    @staticmethod
    def parse(module_path: Path) -> ParsedManifest:
        """
        Locate, load, and validate the manifest.yaml inside *module_path*.

        Validation order:
          1. File existence
          2. Valid YAML
          3. Required fields present (including icon, order)
          4. id format (snake_case)
          5. Semver fields
          6. icon format (kebab-case lucide name)
          7. order is a non-negative integer
          8. color is a known design-system accent (when provided)
          9. platform_min ≤ platform_max

        Args:
            module_path: Absolute or relative path to the module root directory.

        Returns:
            ParsedManifest with all fields populated.

        Raises:
            ManifestError: on any structural or semantic violation.
        """
        manifest_file = module_path / "manifest.yaml"

        # ── 1. File existence ─────────────────────────────────────────────────
        if not manifest_file.exists():
            raise ManifestError(
                f"manifest.yaml not found in module directory: {module_path}"
            )

        # ── 2. YAML parse ─────────────────────────────────────────────────────
        try:
            raw: dict = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ManifestError(f"manifest.yaml is not valid YAML: {exc}") from exc

        if not isinstance(raw, dict):
            raise ManifestError("manifest.yaml must be a YAML mapping at the top level.")

        # ── 3. Required fields ────────────────────────────────────────────────
        missing = [f for f in REQUIRED_FIELDS if raw.get(f) is None or raw.get(f) == ""]
        if missing:
            raise ManifestError(
                f"manifest.yaml is missing required fields: {', '.join(missing)}"
            )

        # ── 4. id format ──────────────────────────────────────────────────────
        module_id = str(raw["id"]).strip()
        if not re.match(r"^[a-z][a-z0-9_]{1,63}$", module_id):
            raise ManifestError(
                f"Module id must be lowercase snake_case, 2-64 chars, got: {module_id!r}"
            )

        # ── 5. Semver validation ──────────────────────────────────────────────
        _assert_semver(str(raw["version"]), "version")

        platform_min = str(raw.get("platform_min_version", "0.0.0"))
        platform_max = str(raw.get("platform_max_version", "999.999.999"))
        _assert_semver(platform_min, "platform_min_version")
        _assert_semver(platform_max, "platform_max_version")

        if _version_tuple(platform_min) > _version_tuple(platform_max):
            raise ManifestError(
                f"platform_min_version ({platform_min}) must be ≤ platform_max_version ({platform_max})"
            )

        # ── 6. icon format ────────────────────────────────────────────────────
        icon_value = str(raw["icon"]).strip()
        if not _ICON_RE.match(icon_value):
            raise ManifestError(
                f"Field 'icon' must be a kebab-case lucide-react icon name "
                f"(e.g. 'shield-check', 'database'), got: {icon_value!r}"
            )

        # ── 7. order must be a non-negative integer ───────────────────────────
        try:
            order_value = int(raw["order"])
        except (ValueError, TypeError):
            raise ManifestError(
                f"Field 'order' must be a non-negative integer, got: {raw['order']!r}"
            )
        if order_value < 0:
            raise ManifestError(
                f"Field 'order' must be ≥ 0, got: {order_value}"
            )

        # ── 8. color validation (optional) ────────────────────────────────────
        color_value: Optional[str] = None
        if raw.get("color"):
            color_value = str(raw["color"]).strip().lower()
            if color_value not in VALID_COLORS:
                raise ManifestError(
                    f"Field 'color' must be one of {sorted(VALID_COLORS)}, "
                    f"got: {color_value!r}"
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
            icon=icon_value,
            order=order_value,
            color=color_value,
            platform_min_version=platform_min,
            platform_max_version=platform_max,
            homepage=raw.get("homepage") or None,
            documentation=raw.get("documentation") or None,
            **_parse_documentation_versioning(raw),
            signature=raw.get("signature") or None,
            checksum=raw.get("checksum") or None,
            raw=raw,
        )
