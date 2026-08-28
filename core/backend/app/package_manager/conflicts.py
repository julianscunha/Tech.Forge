"""
Conflict detection for packages available from multiple sources.

Identifies when the same module_id is available from more than one
catalog source, preventing silent shadowing or duplication.
"""

from app.package_manager.models import PackageInfo


def detect_conflicts(packages: list[PackageInfo]) -> dict[str, list[PackageInfo]]:
    """
    Detect modules available in multiple sources.

    Groups packages by module_id and returns only those that have
    packages from different CatalogSource values.

    Args:
        packages: List of PackageInfo objects to analyze.

    Returns:
        Dict mapping module_id -> list of PackageInfo objects,
        only for modules appearing in more than one source.
        If a module_id appears multiple times in the same source,
        that's not a conflict and is excluded from the result.
    """
    # Group by module_id
    by_module_id: dict[str, list[PackageInfo]] = {}
    for pkg in packages:
        if pkg.module_id not in by_module_id:
            by_module_id[pkg.module_id] = []
        by_module_id[pkg.module_id].append(pkg)

    # Filter to only those with packages from different sources
    conflicts = {}
    for module_id, pkgs in by_module_id.items():
        # Get unique sources for this module_id
        sources = {pkg.source for pkg in pkgs}
        # If more than one source, it's a conflict
        if len(sources) > 1:
            conflicts[module_id] = pkgs

    return conflicts
