"""
Catalog source enumeration.

Identifies where a module package comes from, enabling conflict detection
when the same module_id appears in multiple sources.
"""

from enum import Enum


class CatalogSource(str, Enum):
    """Sources from which packages can be discovered."""

    LOCAL = "local"
    """Built-in repository in modules/repository/ (always available)."""

    OFFICIAL_CATALOG = "official_catalog"
    """Official Tech.Forge module catalog (index.json from canonical source)."""

    CUSTOM_CATALOG = "custom_catalog"
    """User-configured third-party repository (GitHub or compatible API)."""
