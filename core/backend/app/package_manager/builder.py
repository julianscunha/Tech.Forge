"""
Package Builder
===============
Builds a .mod file (structured ZIP) from a validated module directory.

The .mod format:
  <module_id>-<version>.mod
  ├── manifest.yaml        ← at root of archive
  ├── backend/             ← module backend source
  ├── frontend/            ← module frontend source
  ├── assets/
  ├── docs/
  └── META-INF/
      ├── TECHFORGE        ← format marker
      └── BUILD            ← build metadata

Lives in the Core (not the CLI) because the Package Manager needs it at
runtime — e.g. CustomCatalogProvider.fetch_mod_path() (Fase 11) builds a
.mod on the fly from files fetched from a remote git source. The CLI's
`techforge package-module`/`catalog build-index` commands import it from
here (Core → CLI is a one-way dependency in this project; never the
reverse).

Phase 5 extension: the packager will call a signing service here
and embed the signature + checksum into META-INF/SIGNATURE.

Usage:
    from app.package_manager.builder import PackageBuilder
    from pathlib import Path

    result = PackageBuilder.build(module_path=Path("modules/installed/hello_world"))
    print(result.output_path)   # hello_world-1.0.0.mod
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

# ── Excluded patterns ─────────────────────────────────────────────────────────

EXCLUDE_PATTERNS = {
    "__pycache__", ".pyc", ".pyo", ".pyd",
    "node_modules", ".git", "dist", ".DS_Store",
    "*.egg-info", ".venv", "venv",
}

def _should_exclude(path: Path) -> bool:
    name = path.name
    return (
        name.startswith(".")
        or any(name == pat or name.endswith(pat.lstrip("*"))
               for pat in EXCLUDE_PATTERNS)
    )


# ── Build result ──────────────────────────────────────────────────────────────

@dataclass
class BuildResult:
    module_id:   str
    version:     str
    output_path: Path
    file_count:  int
    size_bytes:  int
    checksum:    str    # SHA-256 of the .mod file — Phase 5: signed over this

    @property
    def size_human(self) -> str:
        kb = self.size_bytes / 1024
        return f"{kb:.1f} KB" if kb < 1024 else f"{kb/1024:.2f} MB"


# ── Builder ───────────────────────────────────────────────────────────────────

class PackageBuilder:
    """Builds a .mod package from a module directory."""

    @staticmethod
    def build(
        module_path: Path,
        output_dir: Optional[Path] = None,
    ) -> BuildResult:
        """
        Package *module_path* into a .mod archive.

        Args:
            module_path: Absolute or relative path to module root.
            output_dir:  Where to write the .mod file.
                         Defaults to the current working directory.

        Returns:
            BuildResult with output path, file count, and checksum.

        Raises:
            FileNotFoundError: if module_path or manifest.yaml doesn't exist.
            ValueError:        if manifest.yaml is missing required fields.
        """
        module_path = module_path.resolve()
        manifest_file = module_path / "manifest.yaml"

        if not manifest_file.exists():
            raise FileNotFoundError(f"manifest.yaml not found in {module_path}")

        raw = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
        module_id = raw.get("id")
        version   = raw.get("version")

        if not module_id or not version:
            raise ValueError("manifest.yaml must have 'id' and 'version' fields.")

        if output_dir is None:
            output_dir = Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        archive_name = f"{module_id}-{version}.mod"
        archive_path = output_dir / archive_name

        file_count = 0
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:

            # ── Module files ──────────────────────────────────────────────────
            for src_file in sorted(module_path.rglob("*")):
                if src_file.is_file() and not _should_exclude(src_file):
                    arc_name = src_file.relative_to(module_path)
                    zf.write(src_file, arc_name)
                    file_count += 1

            # ── META-INF/TECHFORGE ────────────────────────────────────────────
            zf.writestr(
                "META-INF/TECHFORGE",
                "TECHFORGE_MODULE_FORMAT=1.0\n"
                f"MIN_PLATFORM_VERSION={raw.get('platform_min_version', '1.0.0')}\n"
            )

            # ── META-INF/BUILD ────────────────────────────────────────────────
            build_meta = {
                "module_id":   module_id,
                "version":     version,
                "built_at":    datetime.now(timezone.utc).isoformat(),
                "file_count":  file_count,
                "format":      "techforge-mod-v1",
                # Phase 5: add "signature" and "signer" fields here
            }
            zf.writestr("META-INF/BUILD", json.dumps(build_meta, indent=2))

        # ── Compute checksum of the final archive ─────────────────────────────
        sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()

        # Write sidecar checksum file (Phase 5: replaced by cryptographic signature)
        (output_dir / f"{archive_name}.sha256").write_text(
            f"{sha256}  {archive_name}\n", encoding="utf-8"
        )

        return BuildResult(
            module_id=module_id,
            version=version,
            output_path=archive_path,
            file_count=file_count,
            size_bytes=archive_path.stat().st_size,
            checksum=sha256,
        )
