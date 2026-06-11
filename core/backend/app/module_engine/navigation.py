"""
Navigation Tree Builder
========================
Builds the hierarchical navigation structure from the in-memory registry:

    category
    └── vendor
        └── module (ordered by `order` field)

This is consumed by:
  - GET /api/v1/registry/navigation  → frontend Sidebar auto-builder
  - GET /api/v1/registry/summary     → extended with category tree

Rules (§7.1):
  - Modules are grouped first by category, then by vendor within each category.
  - Within each vendor group, modules are sorted ascending by `order`.
  - Tie-breaking on `order` is resolved alphabetically by `name`.
  - Only INSTALLED modules appear in navigation (INVALID / INCOMPATIBLE are excluded).
  - The Core owns all navigation composition — modules provide metadata only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import ModuleRegistry, registry as _global_registry


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class NavModuleNode:
    """Leaf node — one installed module."""
    module_id: str
    name:      str
    icon:      str
    color:     str | None
    order:     int
    path:      str          # frontend route: /modules/<module_id>
    vendor:    str
    category:  str


@dataclass
class NavVendorNode:
    """Mid-level node — one vendor within a category."""
    vendor:  str
    modules: list[NavModuleNode] = field(default_factory=list)


@dataclass
class NavCategoryNode:
    """Top-level node — one category."""
    category: str
    vendors:  list[NavVendorNode] = field(default_factory=list)

    @property
    def total_modules(self) -> int:
        return sum(len(v.modules) for v in self.vendors)


@dataclass
class NavigationTree:
    """Complete auto-generated navigation tree for all installed modules."""
    categories: list[NavCategoryNode] = field(default_factory=list)

    @property
    def total_modules(self) -> int:
        return sum(c.total_modules for c in self.categories)


# ── Builder ───────────────────────────────────────────────────────────────────

class NavigationBuilder:
    """
    Stateless builder — call build() whenever the registry changes.
    The Sidebar store calls this after every hot-reload.
    """

    @staticmethod
    def build(reg: ModuleRegistry | None = None) -> NavigationTree:
        """
        Build a NavigationTree from all INSTALLED modules in the registry.

        Args:
            reg: Registry to read from. Defaults to the process singleton.

        Returns:
            NavigationTree sorted by category name, then vendor, then order.
        """
        source = reg or _global_registry

        # Only INSTALLED modules participate in navigation
        entries = [
            e for e in source.all()
            if e.status == ModuleStatus.INSTALLED
        ]

        # category → vendor → [modules]
        tree: dict[str, dict[str, list[NavModuleNode]]] = {}

        for entry in entries:
            cat    = entry.category
            vendor = entry.vendor

            if cat not in tree:
                tree[cat] = {}
            if vendor not in tree[cat]:
                tree[cat][vendor] = []

            tree[cat][vendor].append(NavModuleNode(
                module_id=entry.module_id,
                name=entry.name,
                icon=entry.icon or "puzzle",
                color=entry.color,
                order=entry.order if entry.order is not None else 999,
                path=f"/modules/{entry.module_id}",
                vendor=entry.vendor,
                category=entry.category,
            ))

        # Sort modules within each vendor by (order asc, name asc)
        for cat_vendors in tree.values():
            for modules in cat_vendors.values():
                modules.sort(key=lambda m: (m.order, m.name.lower()))

        # Build typed nodes, sorted by category name then vendor name
        categories: list[NavCategoryNode] = []
        for cat_name in sorted(tree.keys()):
            vendors: list[NavVendorNode] = []
            for vendor_name in sorted(tree[cat_name].keys()):
                vendors.append(NavVendorNode(
                    vendor=vendor_name,
                    modules=tree[cat_name][vendor_name],
                ))
            categories.append(NavCategoryNode(
                category=cat_name,
                vendors=vendors,
            ))

        return NavigationTree(categories=categories)
