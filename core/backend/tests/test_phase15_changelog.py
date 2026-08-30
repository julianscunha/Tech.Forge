"""Fase 15 Slice 8 — Changelog & Release Notes (spec §26/§27).

Formato "Keep a Changelog": `## [version] - date` com subseções restritas
a Added/Changed/Fixed/Deprecated/Removed/Known Issues (spec §26).

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase15_changelog.py -q
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.changelog import parse_changelog, validate_changelog

pytestmark = pytest.mark.unit

VALID = """\
# Changelog

## [Unreleased]

## [1.1.0] - 2026-09-01
### Added
- Nova feature X

### Fixed
- Bug Y corrigido

## [1.0.0] - 2026-08-30
### Added
- Release inicial
"""

INVALID_SECTION = """\
# Changelog

## [1.0.0] - 2026-08-30
### Melhorias
- Algo mudou
"""

MISSING_DATE = """\
# Changelog

## [1.0.0]
### Added
- Sem data
"""

MALFORMED_VERSION = """\
# Changelog

## [not-a-version] - 2026-08-30
### Added
- x
"""


def test_parses_versions_and_sections():
    entries = parse_changelog(VALID)
    versions = [e.version for e in entries if e.version != "Unreleased"]
    assert versions == ["1.1.0", "1.0.0"]
    entry = next(e for e in entries if e.version == "1.1.0")
    assert set(entry.sections.keys()) == {"Added", "Fixed"}
    assert entry.sections["Added"] == ["Nova feature X"]


def test_valid_changelog_has_no_errors():
    assert validate_changelog(VALID) == []


def test_rejects_unknown_section_header():
    errors = validate_changelog(INVALID_SECTION)
    assert any("Melhorias" in e for e in errors)


def test_rejects_entry_without_date():
    errors = validate_changelog(MISSING_DATE)
    assert any("data" in e.lower() for e in errors)


def test_rejects_malformed_version():
    errors = validate_changelog(MALFORMED_VERSION)
    assert any("not-a-version" in e for e in errors)


def test_root_changelog_file_exists_and_is_valid():
    repo_root = Path(__file__).parent.parent.parent.parent
    changelog_path = repo_root / "CHANGELOG.md"
    assert changelog_path.exists(), "CHANGELOG.md deve existir na raiz do repo (spec §27)"
    assert validate_changelog(changelog_path.read_text(encoding="utf-8")) == []
