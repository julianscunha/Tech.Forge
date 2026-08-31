"""Fase 17 Slice 1 — resource limits na extração de pacotes (spec §16/§18).

Threat model (skill security-and-hardening): Denial of Service via zip
bomb — um .mod de poucos KB pode declarar gigabytes de conteúdo
descomprimido e travar a instalação. Boundary: qualquer .mod recebido
(catálogo remoto ou local) antes de extrair.

Run:  cd core/backend && .venv/Scripts/python.exe -m pytest tests/test_phase17_archive_safety.py -q
"""
from __future__ import annotations

import zipfile

import pytest

from app.package_manager.archive_safety import PackageTooLargeError, safe_extract

pytestmark = pytest.mark.unit


def _make_zip(path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)


def test_extracts_normally_within_limits(tmp_path, monkeypatch):
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MAX_PACKAGE_UNCOMPRESSED_SIZE", 1_000_000)
    monkeypatch.setattr(settings, "MAX_PACKAGE_FILE_COUNT", 100)

    archive = tmp_path / "pkg.zip"
    _make_zip(archive, {"manifest.yaml": b"id: x", "backend/main.py": b"print(1)"})
    dest = tmp_path / "dest"
    dest.mkdir()

    with zipfile.ZipFile(archive) as zf:
        safe_extract(zf, dest)

    assert (dest / "manifest.yaml").is_file()
    assert (dest / "backend" / "main.py").is_file()


def test_blocks_when_uncompressed_size_exceeds_limit(tmp_path, monkeypatch):
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MAX_PACKAGE_UNCOMPRESSED_SIZE", 10)
    monkeypatch.setattr(settings, "MAX_PACKAGE_FILE_COUNT", 100)

    archive = tmp_path / "bomb.zip"
    _make_zip(archive, {"big.bin": b"0" * 1000})
    dest = tmp_path / "dest"
    dest.mkdir()

    with zipfile.ZipFile(archive) as zf, pytest.raises(PackageTooLargeError):
        safe_extract(zf, dest)

    assert list(dest.iterdir()) == []  # nada foi extraído — checagem é ANTES de extrair


def test_blocks_when_file_count_exceeds_limit(tmp_path, monkeypatch):
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MAX_PACKAGE_UNCOMPRESSED_SIZE", 1_000_000)
    monkeypatch.setattr(settings, "MAX_PACKAGE_FILE_COUNT", 3)

    archive = tmp_path / "many.zip"
    _make_zip(archive, {f"f{i}.txt": b"x" for i in range(10)})
    dest = tmp_path / "dest"
    dest.mkdir()

    with zipfile.ZipFile(archive) as zf, pytest.raises(PackageTooLargeError):
        safe_extract(zf, dest)

    assert list(dest.iterdir()) == []


def test_skip_prefix_excluded_from_both_count_and_extraction(tmp_path, monkeypatch):
    from app.core.settings import settings
    monkeypatch.setattr(settings, "MAX_PACKAGE_UNCOMPRESSED_SIZE", 1_000_000)
    monkeypatch.setattr(settings, "MAX_PACKAGE_FILE_COUNT", 1)

    archive = tmp_path / "meta.zip"
    _make_zip(archive, {"META-INF/signature": b"x" * 999999, "manifest.yaml": b"id: x"})
    dest = tmp_path / "dest"
    dest.mkdir()

    with zipfile.ZipFile(archive) as zf:
        safe_extract(zf, dest, skip_prefix="META-INF/")

    assert (dest / "manifest.yaml").is_file()
    assert not (dest / "META-INF").exists()
