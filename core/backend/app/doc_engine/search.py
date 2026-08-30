"""
Documentation Search Engine
=============================
Fast, local full-text search over the indexed documentation.

No external services — pure Python string matching with TF-style scoring.

Search strategy:
  1. Tokenise the query into lowercase terms.
  2. Score each DocEntry by how many terms appear in title (×3), tags (×2),
     and content (×1).
  3. Return top-N results sorted by score descending.

Auto-documentation extension point:
  The DocIndex and SearchEngine are designed to receive additional
  DocEntry objects from SDK decorators / contract parsers in future
  versions. The `add()` method is the integration surface.
"""
from __future__ import annotations

import re

from app.doc_engine.models import DocCategory, DocEntry, SearchResult

# ── Simple tokeniser ──────────────────────────────────────────────────────────

_NON_WORD = re.compile(r"[^\w]+")


def _tokens(text: str) -> list[str]:
    return [t for t in _NON_WORD.split(text.lower()) if len(t) > 1]


# ── Index ─────────────────────────────────────────────────────────────────────

class DocIndex:
    """
    In-memory inverted-index of documentation entries.

    Rebuilt from scratch on every startup and after a module install/remove.

    Auto-documentation extension point:
        Future SDK decorators will call index.add(entry) at module
        enable() time to register function-level documentation.
    """

    def __init__(self) -> None:
        self._entries: dict[str, DocEntry] = {}    # id → entry
        # inverted index: token → set of doc ids
        self._index: dict[str, set[str]] = {}

    def add(self, entry: DocEntry) -> None:
        """Index one DocEntry. Thread-safe for read, not for concurrent writes."""
        self._entries[entry.id] = entry
        # Index title (weight handled at search time)
        for tok in _tokens(entry.title):
            self._index.setdefault(tok, set()).add(entry.id)
        # Index tags
        for tag in entry.tags:
            for tok in _tokens(tag):
                self._index.setdefault(tok, set()).add(entry.id)
        # Index content
        for tok in _tokens(entry.content):
            self._index.setdefault(tok, set()).add(entry.id)

    def remove(self, doc_id: str) -> None:
        """Remove a doc from the index (used after module uninstall)."""
        self._entries.pop(doc_id, None)
        for ids in self._index.values():
            ids.discard(doc_id)

    def clear(self) -> None:
        self._entries.clear()
        self._index.clear()

    def get(self, doc_id: str) -> DocEntry | None:
        return self._entries.get(doc_id)

    def all(self) -> list[DocEntry]:
        return list(self._entries.values())

    def by_category(self, category: DocCategory) -> list[DocEntry]:
        return sorted(
            [e for e in self._entries.values() if e.category == category],
            key=lambda e: (e.order, e.title.lower()),
        )

    def by_module(self, module_id: str) -> list[DocEntry]:
        return [e for e in self._entries.values() if e.module_id == module_id]

    @property
    def total(self) -> int:
        return len(self._entries)


# ── Search engine ─────────────────────────────────────────────────────────────

class DocSearchEngine:
    """
    Full-text search over a DocIndex.

    Usage:
        engine = DocSearchEngine(index)
        results = engine.search("module lifecycle install", limit=10)
    """

    def __init__(self, index: DocIndex) -> None:
        self._index = index

    def search(self, query: str, limit: int = 20) -> list[SearchResult]:
        """
        Search for documents matching *query*.

        Scoring weights:
          - title match:   3 points per matching token
          - tag match:     2 points per matching token
          - content match: 1 point per matching token

        Args:
            query: Free-text search string.
            limit: Maximum number of results to return.

        Returns:
            List of SearchResult sorted by score descending.
        """
        if not query.strip():
            return []

        terms = _tokens(query)
        if not terms:
            return []

        scores: dict[str, float] = {}

        for term in terms:
            # Exact token match
            matching_ids = self._index._index.get(term, set())
            # Prefix match for partial queries (e.g. "mani" matches "manifest")
            for tok, ids in self._index._index.items():
                if tok.startswith(term) and tok != term:
                    matching_ids = matching_ids | ids

            for doc_id in matching_ids:
                entry = self._index.get(doc_id)
                if not entry:
                    continue
                score = 0.0
                title_toks = _tokens(entry.title)
                tag_toks   = _tokens(" ".join(entry.tags))
                content_toks = _tokens(entry.content)

                if term in title_toks:
                    score += 3.0
                elif any(t.startswith(term) for t in title_toks):
                    score += 1.5

                if term in tag_toks:
                    score += 2.0

                # Content frequency (capped at 5 to avoid noise)
                freq = min(content_toks.count(term), 5)
                score += freq * 0.5

                scores[doc_id] = scores.get(doc_id, 0.0) + score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in ranked[:limit]:
            entry = self._index.get(doc_id)
            if entry:
                results.append(SearchResult(
                    doc_id=entry.id,
                    title=entry.title,
                    category=entry.category,
                    excerpt=entry.excerpt,
                    module_id=entry.module_id,
                    score=round(score, 2),
                ))
        return results
