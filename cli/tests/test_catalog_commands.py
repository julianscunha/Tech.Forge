"""Fase 11 Slice 6 — CLI `techforge catalog` commands (list, search, show, sources).

Commands call the Core HTTP API /catalog/* endpoints (read-only).
Mock response shapes here MUST match the real API (app/api/routes/catalog.py,
Slice 5a): items live under "items" (not "modules"), each module uses
"module_id" (not "id"), "is_installed" (not "installed"), and
GET /catalog/sources returns a bare JSON array (not {"sources": [...]}).

Run:  pytest cli/tests/test_catalog_commands.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "sdk" / "python"))
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "core" / "backend"))

from techforge_cli.commands.catalog import catalog_cmd

pytestmark = pytest.mark.integration


@pytest.fixture()
def runner():
    return CliRunner()


# ── Test registration ──────────────────────────────────────────────────────

def test_catalog_group_has_list_subcommand():
    """catalog list subcommand is registered."""
    assert "list" in catalog_cmd.commands


def test_catalog_group_has_search_subcommand():
    """catalog search subcommand is registered."""
    assert "search" in catalog_cmd.commands


def test_catalog_group_has_show_subcommand():
    """catalog show subcommand is registered."""
    assert "show" in catalog_cmd.commands


def test_catalog_group_has_sources_subcommand():
    """catalog sources subcommand is registered."""
    assert "sources" in catalog_cmd.commands


def test_catalog_group_has_build_index_subcommand():
    """build-index subcommand moved into catalog group."""
    assert "build-index" in catalog_cmd.commands


# ── Test catalog list ──────────────────────────────────────────────────────

def test_catalog_list_cmd_with_mock_response(runner):
    """catalog list calls GET /catalog/modules and prints table."""
    mock_response = json.dumps({
        "items": [
            {
                "module_id": "mod1",
                "name": "Module 1",
                "category": "Tools",
                "version": "1.0.0",
                "source": "official_catalog",
                "trust_level": "VERIFIED",
                "is_installed": False,
            },
            {
                "module_id": "mod2",
                "name": "Module 2",
                "category": "Backup",
                "version": "2.0.0",
                "source": "local",
                "trust_level": "TRUSTED",
                "is_installed": True,
            },
        ],
        "total": 2,
        "page": 1,
        "page_size": 24,
        "conflicts": {},
    }).encode("utf-8")

    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = mock_response
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj

        result = runner.invoke(catalog_cmd, ["list"])

    assert result.exit_code == 0, result.output
    assert "Module 1" in result.output or "mod1" in result.output
    assert "Module 2" in result.output or "mod2" in result.output


def test_catalog_list_with_category_filter(runner):
    """catalog list --category filters results."""
    mock_response = json.dumps({
        "items": [
            {
                "module_id": "backup_mod",
                "name": "Backup Tool",
                "category": "Backup",
                "version": "1.0.0",
                "source": "local",
                "trust_level": "TRUSTED",
                "is_installed": False,
            },
        ],
        "total": 1,
        "page": 1,
        "page_size": 24,
        "conflicts": {},
    }).encode("utf-8")

    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = mock_response
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj

        result = runner.invoke(catalog_cmd, ["list", "--category", "Backup"])

    assert result.exit_code == 0, result.output
    # Verify that category param was included in the request
    mock_urlopen.assert_called_once()
    call_args = mock_urlopen.call_args[0][0]
    assert "category=Backup" in str(call_args)


def test_catalog_list_platform_unavailable(runner):
    """catalog list handles platform unavailable gracefully."""
    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = runner.invoke(catalog_cmd, ["list"])

    assert result.exit_code == 1
    assert "Plataforma não acessível" in result.output


# ── Test catalog search ──────────────────────────────────────────────────────

def test_catalog_search_cmd_with_term(runner):
    """catalog search <term> calls GET /catalog/modules?search=<term>."""
    mock_response = json.dumps({
        "items": [
            {
                "module_id": "searchmod",
                "name": "Search Result Module",
                "category": "Tools",
                "version": "1.0.0",
                "source": "local",
                "trust_level": "TRUSTED",
                "is_installed": False,
            },
        ],
        "total": 1,
        "page": 1,
        "page_size": 24,
        "conflicts": {},
    }).encode("utf-8")

    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = mock_response
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj

        result = runner.invoke(catalog_cmd, ["search", "result"])

    assert result.exit_code == 0, result.output
    # Verify search param in URL
    call_args = mock_urlopen.call_args[0][0]
    assert "search=result" in str(call_args)


def test_catalog_search_no_results(runner):
    """catalog search with no matches returns empty table."""
    mock_response = json.dumps({
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 24,
        "conflicts": {},
    }).encode("utf-8")

    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = mock_response
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj

        result = runner.invoke(catalog_cmd, ["search", "nonexistent"])

    assert result.exit_code == 0, result.output


# ── Test catalog show ──────────────────────────────────────────────────────

def test_catalog_show_cmd_with_id(runner):
    """catalog show <id> calls GET /catalog/modules/<id> and prints details."""
    mock_response = json.dumps({
        "module_id": "testmod",
        "name": "Test Module",
        "description": "A test module for Slice 6",
        "version": "1.0.0",
        "category": "Tools",
        "author": "Test Author",
        "publisher": "Test Publisher",
        "source": "local",
        "trust_level": "TRUSTED",
        "is_installed": False,
        "compatibility": "COMPATIBLE",
        "platform_min_version": "0.0.0",
        "platform_max_version": "999.999.999",
    }).encode("utf-8")

    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = mock_response
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj

        result = runner.invoke(catalog_cmd, ["show", "testmod"])

    assert result.exit_code == 0, result.output
    assert "testmod" in result.output or "Test Module" in result.output
    assert "Test Author" in result.output or "author" in result.output.lower()


def test_catalog_show_not_found(runner):
    """catalog show <non-existent-id> returns 404."""
    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        import urllib.error
        http_error = urllib.error.HTTPError(
            url="http://127.0.0.1:8000/api/v1/catalog/modules/ghost",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        # Mock the read() method on the exception
        http_error.read = MagicMock(return_value=b'{"error": "Module not found"}')
        mock_urlopen.side_effect = http_error

        result = runner.invoke(catalog_cmd, ["show", "ghost"])

    assert result.exit_code == 1


# ── Test catalog sources ──────────────────────────────────────────────────────

def test_catalog_sources_cmd(runner):
    """catalog sources calls GET /catalog/sources and prints table.

    GET /catalog/sources returns a bare JSON array (response_model=list[...]),
    not wrapped in {"sources": [...]}.
    """
    mock_response = json.dumps([
        {
            "id": "official",
            "name": "Official Catalog",
            "url": "https://example.com/catalog",
            "type": "official_catalog",
            "enabled": True,
            "status": "available",
        },
        {
            "id": "custom1",
            "name": "My Custom Repo",
            "url": "https://github.com/user/modules",
            "type": "custom_catalog",
            "enabled": True,
            "status": "unavailable",
        },
    ]).encode("utf-8")

    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = mock_response
        mock_urlopen.return_value.__enter__.return_value = mock_response_obj

        result = runner.invoke(catalog_cmd, ["sources"])

    assert result.exit_code == 0, result.output
    assert "Official Catalog" in result.output or "official" in result.output


def test_catalog_sources_platform_unavailable(runner):
    """catalog sources handles platform unavailable."""
    with patch("techforge_cli.commands.catalog.urllib.request.urlopen") as mock_urlopen:
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        result = runner.invoke(catalog_cmd, ["sources"])

    assert result.exit_code == 1
    assert "Plataforma não acessível" in result.output


# ── Test group registration in main CLI ──────────────────────────────────────

def test_catalog_group_registered_in_main_cli():
    """catalog group is registered as a top-level CLI command."""
    from techforge_cli.main import cli
    assert "catalog" in cli.commands
