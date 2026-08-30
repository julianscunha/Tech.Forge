"""
Documentation Indexer
======================
Scans all documentation sources and populates the DocIndex:

  1. Core docs   — docs/developer-center/**/*.md  (shipped with the platform)
  2. Module docs — modules/installed/<id>/docs/**/*.md  (per installed module)
  3. Service contracts — modules/installed/<id>/docs/contracts/api.yaml

Called by:
  - FastAPI lifespan (startup)
  - PackageManager._hot_reload() (after install/remove/update)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.core.settings import settings
from app.doc_engine.api_yaml_parser import APIYamlParser
from app.doc_engine.markdown_parser import MarkdownParser
from app.doc_engine.models import DocCategory, ServiceContract
from app.doc_engine.search import DocIndex

logger = logging.getLogger("techforge.doc_engine")

# Root of the platform docs tree
DOCS_ROOT = settings.BASE_DIR / "docs" / "developer-center"

# Maps subdirectory name → DocCategory
CORE_DOC_DIRS: dict[str, DocCategory] = {
    "core":            DocCategory.ARCHITECTURE,
    "guides":          DocCategory.GUIDE,
    "sdk":             DocCategory.SDK_BACKEND,
    "reference":       DocCategory.MANIFEST_REF,
    "examples":        DocCategory.EXAMPLES,
    "service-modules": DocCategory.SERVICE_MODULE,
    "faq":             DocCategory.FAQ,
    "marketplace":     DocCategory.MARKETPLACE,
    "governance":      DocCategory.GOVERNANCE,
}

# Top-level .md files in docs/developer-center/ → INTRO
_INTRO_FILES = {"intro.md", "index.md", "README.md"}


class DocIndexer:
    """
    Builds and refreshes the DocIndex from all documentation sources.
    """

    def __init__(
        self,
        index: DocIndex,
        docs_root: Optional[Path] = None,
        installed_path: Optional[Path] = None,
    ) -> None:
        self._index         = index
        self._docs_root     = docs_root or DOCS_ROOT
        self._installed     = installed_path or settings.MODULES_INSTALLED_PATH
        self._contracts: dict[str, ServiceContract] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    def rebuild(self) -> int:
        """
        Clear and rebuild the entire index.

        Returns:
            Total number of documents indexed.
        """
        self._index.clear()
        self._contracts.clear()

        count = self._index_core_docs()
        count += self._index_module_docs()

        logger.info(
            "DocIndexer: %d documents indexed (%d service contracts).",
            count, len(self._contracts),
        )
        return count

    def index_module(self, module_id: str) -> int:
        """
        Index (or re-index) documentation for a single module.
        Called by PackageManager after install/update.
        """
        # Remove existing docs for this module first
        for entry in self._index.by_module(module_id):
            self._index.remove(entry.id)
        self._contracts.pop(module_id, None)

        module_path = self._installed / module_id
        return self._index_one_module(module_path)

    def remove_module(self, module_id: str) -> None:
        """Remove all docs for a module. Called after uninstall."""
        for entry in self._index.by_module(module_id):
            self._index.remove(entry.id)
        self._contracts.pop(module_id, None)

    def get_contract(self, module_id: str) -> Optional[ServiceContract]:
        return self._contracts.get(module_id)

    def all_contracts(self) -> list[ServiceContract]:
        return list(self._contracts.values())

    # ── Internal ──────────────────────────────────────────────────────────────

    def _index_core_docs(self) -> int:
        """Scan docs/developer-center/ and index all .md files."""
        if not self._docs_root.exists():
            logger.warning("Core docs root not found: %s", self._docs_root)
            return 0

        count = 0

        # Top-level .md files → INTRO
        for md in sorted(self._docs_root.glob("*.md")):
            try:
                entry = MarkdownParser.parse(
                    path=md,
                    base=self._docs_root,
                    category=DocCategory.INTRO,
                )
                self._index.add(entry)
                count += 1
            except Exception as exc:
                logger.debug("Skipped %s: %s", md, exc)

        # Subdirectory docs
        for subdir_name, category in CORE_DOC_DIRS.items():
            subdir = self._docs_root / subdir_name
            if not subdir.exists():
                continue
            entries = MarkdownParser.parse_many(
                directory=subdir,
                base=self._docs_root,
                category=category,
            )
            for entry in entries:
                self._index.add(entry)
                count += 1

        return count

    def _index_module_docs(self) -> int:
        """Scan all installed modules and index their docs."""
        if not self._installed.exists():
            return 0

        count = 0
        for module_dir in sorted(self._installed.iterdir()):
            if module_dir.is_dir() and not module_dir.name.startswith("."):
                count += self._index_one_module(module_dir)
        return count

    def _index_one_module(self, module_path: Path) -> int:
        module_id = module_path.name
        docs_dir  = module_path / "docs"
        count = 0

        if not docs_dir.exists():
            return 0

        # Parse overview.md and all .md files (excluding contracts/)
        for md in sorted(docs_dir.rglob("*.md")):
            if "contracts" in md.parts:
                continue
            try:
                # §16 — files under docs/examples/ get their own category
                # so the Developer Center and completeness checker can
                # distinguish documentation from worked examples.
                category = (
                    DocCategory.MODULE_EXAMPLE
                    if "examples" in md.parts
                    else DocCategory.MODULE
                )
                entry = MarkdownParser.parse(
                    path=md,
                    base=docs_dir,
                    category=category,
                    module_id=module_id,
                )
                # Prefix ID with module_id to avoid collisions across modules
                entry.id = f"{module_id}/{entry.id}"
                self._index.add(entry)
                count += 1
            except Exception as exc:
                logger.warning(
                    "Failed to index doc for module %s: %s", module_id, exc)

        # Parse contracts/api.yaml
        api_yaml = docs_dir / "contracts" / "api.yaml"
        contract = APIYamlParser.parse(api_yaml, module_id)
        if contract:
            self._contracts[module_id] = contract
            logger.debug("Indexed service contract for '%s'", module_id)

        return count
