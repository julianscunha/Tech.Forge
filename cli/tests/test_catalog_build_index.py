"""Fase 11 Slice 2 — CLI `techforge catalog build-index` command.

Generates index.json and .mod files from a modules directory.

Run:  pytest cli/tests/test_catalog_build_index.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "sdk" / "python"))
sys.path.insert(0, str(ROOT / "cli"))
sys.path.insert(0, str(ROOT / "core" / "backend"))

from techforge_cli.commands.catalog import catalog_cmd


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def modules_dir(tmp_path):
    """Create a directory with 2 valid modules for testing."""
    modules_root = tmp_path / "modules"
    modules_root.mkdir()

    # Module 1: simple_module
    mod1 = modules_root / "simple_module"
    (mod1 / "backend").mkdir(parents=True)
    (mod1 / "frontend").mkdir(parents=True)
    (mod1 / "docs").mkdir(parents=True)
    (mod1 / "backend" / "api.py").write_text("router = None\n", encoding="utf-8")
    (mod1 / "frontend" / "main.js").write_text("export default {};\n", encoding="utf-8")
    (mod1 / "manifest.yaml").write_text(
        """
id: simple_module
name: Simple Module
version: 1.0.0
description: A simple test module
category: Examples
vendor: TestVendor
author: TestAuthor
module_type: application
""",
        encoding="utf-8",
    )

    # Module 2: another_module
    mod2 = modules_root / "another_module"
    (mod2 / "backend").mkdir(parents=True)
    (mod2 / "frontend").mkdir(parents=True)
    (mod2 / "docs").mkdir(parents=True)
    (mod2 / "backend" / "service.py").write_text("class Service: pass\n", encoding="utf-8")
    (mod2 / "frontend" / "app.js").write_text("export default {};\n", encoding="utf-8")
    (mod2 / "manifest.yaml").write_text(
        """
id: another_module
name: Another Module
version: 2.0.0
description: Another test module
category: Tools
vendor: TestVendor
author: TestAuthor
module_type: application
""",
        encoding="utf-8",
    )

    return modules_root


def test_build_index_creates_index_json(runner, modules_dir, tmp_path):
    """build-index command creates index.json with correct structure."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(
        catalog_cmd,
        ["build-index", str(modules_dir), "--output", str(output_dir)],
    )

    assert result.exit_code == 0, f"Command failed: {result.output}"

    # Check that index.json was created
    index_file = output_dir / "index.json"
    assert index_file.exists(), f"index.json not created in {output_dir}"

    # Parse and verify structure
    index_data = json.loads(index_file.read_text(encoding="utf-8"))
    assert "modules" in index_data
    assert len(index_data["modules"]) == 2


def test_build_index_generates_mod_files(runner, modules_dir, tmp_path):
    """build-index command generates .mod files for each module."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(
        catalog_cmd,
        ["build-index", str(modules_dir), "--output", str(output_dir)],
    )

    assert result.exit_code == 0

    # .mod files nest under a per-module folder (output_dir/<id>/<id>-<version>.mod)
    # so every version ever built for a module stays alongside its siblings —
    # a new PR/version never overwrites or orphans the previous one.
    mod_files = list(output_dir.glob("*/*.mod"))
    assert len(mod_files) == 2
    assert any("simple_module" in f.name for f in mod_files)
    assert any("another_module" in f.name for f in mod_files)
    assert (output_dir / "simple_module" / "simple_module-1.0.0.mod").exists()
    assert (output_dir / "another_module" / "another_module-2.0.0.mod").exists()


def test_build_index_correct_module_metadata(runner, modules_dir, tmp_path):
    """index.json contains correct metadata from manifests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(
        catalog_cmd,
        ["build-index", str(modules_dir), "--output", str(output_dir)],
    )

    assert result.exit_code == 0

    index_data = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
    modules = {m["id"]: m for m in index_data["modules"]}

    # Verify simple_module metadata
    assert modules["simple_module"]["name"] == "Simple Module"
    assert modules["simple_module"]["version"] == "1.0.0"
    assert modules["simple_module"]["category"] == "Examples"
    assert modules["simple_module"]["vendor"] == "TestVendor"
    assert modules["simple_module"]["author"] == "TestAuthor"
    assert "simple_module-1.0.0.mod" in modules["simple_module"]["mod_url"]

    # Verify another_module metadata
    assert modules["another_module"]["name"] == "Another Module"
    assert modules["another_module"]["version"] == "2.0.0"
    assert modules["another_module"]["category"] == "Tools"


def test_build_index_includes_checksum(runner, modules_dir, tmp_path):
    """index.json includes checksum for each module."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(
        catalog_cmd,
        ["build-index", str(modules_dir), "--output", str(output_dir)],
    )

    assert result.exit_code == 0

    index_data = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))
    modules = {m["id"]: m for m in index_data["modules"]}

    # Each module should have a checksum (SHA-256)
    assert "checksum" in modules["simple_module"]
    assert len(modules["simple_module"]["checksum"]) == 64  # SHA-256 hex length
    assert "checksum" in modules["another_module"]
    assert len(modules["another_module"]["checksum"]) == 64


def test_build_index_round_trip_validation(runner, modules_dir, tmp_path):
    """Generated .mod files are valid and readable."""
    import zipfile

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    result = runner.invoke(
        catalog_cmd,
        ["build-index", str(modules_dir), "--output", str(output_dir)],
    )

    assert result.exit_code == 0

    # Each .mod file should be a valid ZIP with manifest.yaml
    for mod_file in output_dir.glob("*/*.mod"):
        try:
            with zipfile.ZipFile(mod_file) as zf:
                assert "manifest.yaml" in zf.namelist()
                # Manifest should be readable
                manifest_content = zf.read("manifest.yaml")
                assert len(manifest_content) > 0
        except zipfile.BadZipFile:
            pytest.fail(f"{mod_file.name} is not a valid ZIP archive")
