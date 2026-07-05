"""
Documentation Engine — Data Models
=====================================
Shared data structures used across the Documentation Engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class DocCategory(str, Enum):
    """Top-level categories matching Developer Center sections."""
    INTRO          = "intro"
    ARCHITECTURE   = "architecture"
    GUIDE          = "guide"
    SDK_BACKEND    = "sdk-backend"
    SDK_FRONTEND   = "sdk-frontend"
    SERVICE_MODULE = "service-module"
    EXAMPLES       = "examples"
    MANIFEST_REF   = "manifest-reference"
    MARKETPLACE    = "marketplace"
    FAQ            = "faq"
    MODULE         = "module"          # auto-indexed from installed modules
    MODULE_EXAMPLE = "module-example"   # per-module examples/{basic,advanced,integration}.md
    GOVERNANCE     = "governance"       # §16 Documentation First Principle docs


class ExampleTier(str, Enum):
    """§16 — the three mandatory example tiers for service modules."""
    BASIC       = "basic"
    ADVANCED    = "advanced"
    INTEGRATION = "integration"


@dataclass
class DocEntry:
    """
    One documentation article indexed by the Documentation Engine.
    """
    id:       str              # unique slug — e.g. "core/app-shell"
    title:    str
    category: DocCategory
    content:  str              # raw Markdown source
    path:     Path             # absolute path to the .md file
    module_id: Optional[str] = None   # set when the doc comes from a module
    order:    int = 99
    tags:     list[str] = field(default_factory=list)

    @property
    def excerpt(self) -> str:
        """First 200 non-empty characters of content, without Markdown syntax."""
        import re
        plain = re.sub(r"[#`*_\[\]()>]+", "", self.content)
        plain = " ".join(plain.split())
        return plain[:200]


@dataclass
class SearchResult:
    """One hit returned by DocSearchEngine.search()."""
    doc_id:   str
    title:    str
    category: DocCategory
    excerpt:  str
    module_id: Optional[str]
    score:    float            # relevance score (higher = better)


# ── Service contract models ───────────────────────────────────────────────────

@dataclass
class ServiceExport:
    name:        str
    description: str
    parameters:  list[dict] = field(default_factory=list)
    returns:     Optional[str] = None
    examples:    list[str]  = field(default_factory=list)


@dataclass
class ServiceContract:
    """
    Parsed representation of a module's contracts/api.yaml.
    """
    service_id:  str
    module_id:   str
    description: str
    version:     str = "1.0.0"
    exports:     list[ServiceExport] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    raw:         dict = field(default_factory=dict)
