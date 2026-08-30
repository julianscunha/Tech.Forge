"""Fase 15 §26/§27 — parser e validador de CHANGELOG.md (formato "Keep a Changelog").

`## [version] - YYYY-MM-DD` (ou `## [Unreleased]`, sem data), com subseções
restritas a Added/Changed/Fixed/Deprecated/Removed/Known Issues (spec §26).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from packaging.version import InvalidVersion, Version

ALLOWED_SECTIONS = {"Added", "Changed", "Fixed", "Deprecated", "Removed", "Known Issues"}

_VERSION_HEADER_RE = re.compile(r"^##\s*\[([^\]]+)\](?:\s*-\s*(\d{4}-\d{2}-\d{2}))?\s*$")
_SECTION_HEADER_RE = re.compile(r"^###\s*(.+?)\s*$")
_ITEM_RE = re.compile(r"^-\s+(.+)$")


@dataclass
class ChangelogEntry:
    version: str
    date: str | None
    sections: dict[str, list[str]] = field(default_factory=dict)


def parse_changelog(text: str) -> list[ChangelogEntry]:
    entries: list[ChangelogEntry] = []
    current: ChangelogEntry | None = None
    current_section: str | None = None

    for line in text.splitlines():
        version_match = _VERSION_HEADER_RE.match(line)
        if version_match:
            current = ChangelogEntry(version=version_match.group(1), date=version_match.group(2))
            entries.append(current)
            current_section = None
            continue

        if current is None:
            continue

        section_match = _SECTION_HEADER_RE.match(line)
        if section_match:
            current_section = section_match.group(1)
            current.sections.setdefault(current_section, [])
            continue

        item_match = _ITEM_RE.match(line)
        if item_match and current_section:
            current.sections[current_section].append(item_match.group(1))

    return entries


def validate_changelog(text: str) -> list[str]:
    errors: list[str] = []
    for entry in parse_changelog(text):
        if entry.version != "Unreleased":
            if entry.date is None:
                errors.append(f"Versão '{entry.version}' sem data (spec §27 exige YYYY-MM-DD)")
            try:
                Version(entry.version)
            except InvalidVersion:
                errors.append(f"Versão '{entry.version}' não é um SemVer válido")

        unknown = set(entry.sections) - ALLOWED_SECTIONS
        if unknown:
            errors.append(
                f"Versão '{entry.version}': seção(ões) desconhecida(s) {sorted(unknown)} "
                f"— permitidas: {sorted(ALLOWED_SECTIONS)}"
            )
    return errors
