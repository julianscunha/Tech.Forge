"""
Markdown Parser
================
Reads .md files, optionally parses YAML frontmatter, and returns a
structured DocEntry ready for indexing.

Frontmatter format (optional):
    ---
    title: My Page Title
    order: 5
    tags: [sdk, backend, contracts]
    ---

If no frontmatter title is present, the first H1 heading is used.
If no H1 is found, the filename stem is used.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from app.doc_engine.models import DocCategory, DocEntry

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# ── Frontmatter extraction ────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_without_frontmatter)."""
    m = _FRONTMATTER_RE.match(text)
    if not m or not _HAS_YAML:
        return {}, text
    try:
        meta = _yaml.safe_load(m.group(1)) or {}
    except Exception:
        meta = {}
    body = text[m.end():]
    return meta, body


def _extract_h1(text: str) -> Optional[str]:
    """Return the first H1 heading text, or None."""
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def _slug(path: Path, base: Path) -> str:
    """
    Create a stable doc ID from the file path relative to base.
    e.g. docs/developer-center/core/app-shell.md → core/app-shell
    """
    try:
        rel = path.relative_to(base)
    except ValueError:
        rel = path
    parts = list(rel.with_suffix("").parts)
    return "/".join(parts)


# ── Public API ────────────────────────────────────────────────────────────────

class MarkdownParser:
    """
    Parses a single .md file into a DocEntry.

    Usage:
        entry = MarkdownParser.parse(
            path=Path("docs/developer-center/core/app-shell.md"),
            base=Path("docs/developer-center"),
            category=DocCategory.ARCHITECTURE,
        )
    """

    @staticmethod
    def parse(
        path: Path,
        base: Path,
        category: DocCategory,
        module_id: Optional[str] = None,
        default_order: int = 99,
    ) -> DocEntry:
        """
        Read and parse a Markdown file.

        Args:
            path:          Absolute path to the .md file.
            base:          Root directory used to compute the doc ID.
            category:      DocCategory for this document.
            module_id:     Set when the doc comes from an installed module.
            default_order: Fallback sort order when frontmatter has none.

        Returns:
            DocEntry with all fields populated.
        """
        raw = path.read_text(encoding="utf-8", errors="replace")
        meta, body = _parse_frontmatter(raw)

        title = (
            meta.get("title")
            or _extract_h1(body)
            or path.stem.replace("-", " ").replace("_", " ").title()
        )

        order = int(meta.get("order", default_order))
        tags  = list(meta.get("tags", []))

        doc_id = _slug(path, base)

        return DocEntry(
            id=doc_id,
            title=str(title).strip(),
            category=category,
            content=body.strip(),
            path=path,
            module_id=module_id,
            order=order,
            tags=tags,
        )

    @staticmethod
    def parse_many(
        directory: Path,
        base: Path,
        category: DocCategory,
        module_id: Optional[str] = None,
        glob: str = "**/*.md",
    ) -> list[DocEntry]:
        """
        Parse all .md files in *directory* matching *glob*.
        Returns entries sorted by (order, title).
        """
        entries = []
        for md_file in sorted(directory.glob(glob)):
            try:
                entry = MarkdownParser.parse(
                    path=md_file,
                    base=base,
                    category=category,
                    module_id=module_id,
                )
                entries.append(entry)
            except Exception:
                pass   # skip unreadable files silently
        entries.sort(key=lambda e: (e.order, e.title.lower()))
        return entries
