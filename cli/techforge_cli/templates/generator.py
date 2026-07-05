"""
TechForge CLI — Template Generator
=====================================
Generates a complete module scaffold from the official templates,
substituting module-specific values via Jinja2.

Called by: techforge create-module
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, BaseLoader


# ── Module spec ───────────────────────────────────────────────────────────────

@dataclass
class ModuleSpec:
    """All values collected from the user during `techforge create-module`."""
    id: str             # snake_case identifier
    name: str           # Human-readable display name
    category: str       # Module category (must match a registered Core category)
    vendor: str         # Vendor / company name
    author: str         # Author full name
    description: str    # One-line description
    icon: str = "puzzle"
    color: str = "blue"
    order: int = 10
    platform_min: str = "1.0.0"
    platform_max: str = "999.999.999"
    version: str = "1.0.0"

    def validate(self) -> list[str]:
        errors = []
        if not re.match(r"^[a-z][a-z0-9_]{1,63}$", self.id):
            errors.append("Module id must be lowercase snake_case (e.g. my_module).")
        if not self.name.strip():
            errors.append("Module name cannot be empty.")
        if not self.category.strip():
            errors.append("Category cannot be empty.")
        if not self.vendor.strip():
            errors.append("Vendor cannot be empty.")
        if not re.match(r"^\d+\.\d+\.\d+$", self.version):
            errors.append("Version must follow semver (X.Y.Z).")
        return errors


# ── Jinja2 template sources ───────────────────────────────────────────────────

MANIFEST_TEMPLATE = """\
id: {{ spec.id }}
name: {{ spec.name }}
version: {{ spec.version }}

platform_min_version: {{ spec.platform_min }}
platform_max_version: {{ spec.platform_max }}

category: {{ spec.category }}
vendor: {{ spec.vendor }}
author: {{ spec.author }}
description: >
  {{ spec.description }}

# Navigation & Presentation (§7.1) — required
icon: {{ spec.icon }}
order: {{ spec.order }}

# Optional presentation
color: {{ spec.color }}

entry_backend: backend/main.py
entry_frontend: frontend/index.tsx

homepage:
documentation:

# Security fields — populated by Marketplace in Phase 5
signature:
checksum:
"""

BACKEND_MAIN_TEMPLATE = """\
\"\"\"
{{ spec.name }} — Backend Entry Point
{{ '=' * (len(spec.name) + 26) }}
Module ID : {{ spec.id }}
Category  : {{ spec.category }}
Vendor    : {{ spec.vendor }}
Author    : {{ spec.author }}

Replace this stub with your real implementation.
\"\"\"
from fastapi import APIRouter
from techforge_sdk import create_sdk
from techforge_sdk.contracts import ModuleContract, ModuleMetadata, HealthResult

# ── SDK — scoped to this module ───────────────────────────────────────────────
sdk = create_sdk("{{ spec.id }}")

# ── FastAPI router — mounted by Plugin Loader at /api/v1/modules/{{ spec.id }} ─
router = APIRouter(prefix="/modules/{{ spec.id }}", tags=["{{ spec.id }}"])


@router.get("/ping")
async def ping():
    \"\"\"Health endpoint — required by the Platform.\"\"\"
    return {"module": "{{ spec.id }}", "status": "ok", "version": "{{ spec.version }}"}


# ── Module contract implementation ────────────────────────────────────────────

class {{ spec.id | title_case }}Module(ModuleContract):

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            id="{{ spec.id }}",
            name="{{ spec.name }}",
            version="{{ spec.version }}",
            category="{{ spec.category }}",
            vendor="{{ spec.vendor }}",
            author="{{ spec.author }}",
            description="{{ spec.description }}",
            platform_min_version="{{ spec.platform_min }}",
            platform_max_version="{{ spec.platform_max }}",
        )

    async def install(self) -> None:
        sdk.logger.info("Installing {{ spec.name }}…")
        # TODO: create tables, default settings, initial data

    async def enable(self) -> None:
        sdk.logger.info("{{ spec.name }} enabled.")
        # TODO: start background tasks, open connections

    async def disable(self) -> None:
        sdk.logger.info("{{ spec.name }} disabled.")
        # TODO: stop tasks, release connections

    async def upgrade(self, from_version: str) -> None:
        sdk.logger.info("Upgrading {{ spec.name }} from %s…", from_version)
        # TODO: run migrations

    async def health_check(self) -> HealthResult:
        return HealthResult.ok("{{ spec.name }} is healthy.")

    async def uninstall(self) -> None:
        sdk.logger.info("Uninstalling {{ spec.name }}…")
        sdk.settings.reset()
        # TODO: drop tables, delete files


module = {{ spec.id | title_case }}Module()
"""

FRONTEND_TEMPLATE = """\
/**
 * {{ spec.name }} — Frontend Entry Point
 * {{ '=' * (spec.name | length + 26) }}
 * Module    : {{ spec.id }}
 * Category  : {{ spec.category }}
 * Vendor    : {{ spec.vendor }}
 *
 * Replace this stub with your real UI.
 */
import {
  ModulePage,
  PageHeader,
  Card,
  EmptyState,
} from '@techforge/sdk'
import type { ModulePageConfig } from '@techforge/sdk'

// ── Module config — read by Plugin Loader ─────────────────────────────────────
export const moduleConfig: ModulePageConfig = {
  moduleId:    "{{ spec.id }}",
  title:       "{{ spec.name }}",
  icon:        "Boxes",
  category:    "{{ spec.category }}",
  vendor:      "{{ spec.vendor }}",
  route:       "/modules/{{ spec.id }}",
  description: "{{ spec.description }}",
}

// ── Page component ────────────────────────────────────────────────────────────
export default function {{ spec.id | component_name }}Page() {
  return (
    <ModulePage>
      <PageHeader
        title="{{ spec.name }}"
        description="{{ spec.description }}"
      />
      <Card>
        <EmptyState
          title="Módulo em desenvolvimento"
          description="Implemente seu conteúdo aqui usando os componentes do SDK."
        />
      </Card>
    </ModulePage>
  )
}

// ── Lifecycle hooks ───────────────────────────────────────────────────────────
export function onMount(): void {
  // Initialize module state
}

export function onUnmount(): void {
  // Cleanup
}
"""

README_TEMPLATE = """\
# {{ spec.name }}

**Category:** {{ spec.category }}
**Vendor:**   {{ spec.vendor }}
**Author:**   {{ spec.author }}
**Version:**  {{ spec.version }}

## Description

{{ spec.description }}

## Getting Started

This module was scaffolded with `techforge create-module`.

### Backend

The backend entry point is `backend/main.py`.
It implements `ModuleContract` from `techforge_sdk`.

```bash
# Install the SDK
pip install -e ../../sdk/python

# Run tests
pytest tests/
```

### Frontend

The frontend entry point is `frontend/index.tsx`.
It exports `moduleConfig` and a default React component.

```bash
# SDK components are available via @techforge/sdk
import { Card, PageHeader, DataTable } from '@techforge/sdk'
```

## Validate

```bash
techforge validate-module .
```

## Package

```bash
techforge package-module .
# Output: {{ spec.id }}-{{ spec.version }}.mod
```

## Structure

```
{{ spec.id }}/
├── manifest.yaml
├── backend/
│   └── main.py
├── frontend/
│   └── index.tsx
├── assets/
├── docs/
│   ├── README.md
│   ├── overview.md
│   └── examples/
│       └── basic.md
└── tests/
    └── test_module.py
```
"""

# ── §16 Documentation First Principle ─────────────────────────────────────────
# Every scaffolded module ships with overview.md and examples/basic.md so it
# passes `techforge validate-module` immediately. Edit these to describe your
# actual implementation before publishing.

OVERVIEW_TEMPLATE = """\
---
title: {{ spec.name }} — Overview
order: 1
tags: [{{ spec.id }}, {{ spec.category | lower }}]
---

# {{ spec.name }}

**Category:** {{ spec.category }}
**Vendor:** {{ spec.vendor }}
**Version:** {{ spec.version }}

## Descrição

{{ spec.description }}

## O que faz

- TODO: descreva a primeira funcionalidade principal
- TODO: descreva a segunda funcionalidade principal

## Quando usar

TODO: descreva o caso de uso ideal para este módulo.

## Configuração

TODO: liste as settings obrigatórias, se houver:
- `setting_key` (tipo): descrição
"""

BASIC_EXAMPLE_TEMPLATE = """\
---
title: {{ spec.name }} — Exemplo Básico
order: 1
tags: [{{ spec.id }}, basic, example]
---

## Objetivo

TODO: descreva o uso mínimo deste módulo.

## Entradas

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| TODO | TODO | TODO | TODO |

## Saídas

```json
{
  "status": "ok"
}
```

## Exemplo

```python
from techforge_sdk import create_sdk
sdk = create_sdk("{{ spec.id }}")

# TODO: substitua pelo uso real do seu módulo
```

## Observações

TODO: adicione observações relevantes sobre este exemplo.
"""


TEST_TEMPLATE = """\
\"\"\"
{{ spec.name }} — Test Suite
{{ '=' * (len(spec.name) + 16) }}
Run with: pytest tests/
\"\"\"
import asyncio
import pytest
from pathlib import Path


# ── Import module under test ──────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.main import module, router


# ── Metadata tests ────────────────────────────────────────────────────────────

def test_metadata_id():
    assert module.metadata.id == "{{ spec.id }}"

def test_metadata_version():
    import re
    assert re.match(r"^\\d+\\.\\d+\\.\\d+$", module.metadata.version)

def test_metadata_required_fields():
    m = module.metadata
    assert m.name and m.category and m.vendor and m.author and m.description


# ── Lifecycle tests ───────────────────────────────────────────────────────────

def test_install_is_idempotent():
    asyncio.run(module.install())
    asyncio.run(module.install())  # Should not raise

def test_enable_disable_cycle():
    asyncio.run(module.enable())
    asyncio.run(module.disable())

def test_health_check_returns_result():
    from techforge_sdk.contracts import HealthResult
    result = asyncio.run(module.health_check())
    assert isinstance(result, HealthResult)

def test_upgrade_runs_without_error():
    asyncio.run(module.upgrade("0.9.0"))


# ── Router tests ──────────────────────────────────────────────────────────────

def test_router_has_ping_route():
    routes = [r.path for r in router.routes]
    assert any("ping" in r for r in routes)
"""


# ── Generator ─────────────────────────────────────────────────────────────────

def _title_case(value: str) -> str:
    """snake_case → TitleCase for class names."""
    return "".join(word.capitalize() for word in value.split("_"))


def _component_name(value: str) -> str:
    """snake_case → ComponentName."""
    return _title_case(value)


def _repeat(value: str, n: int) -> str:
    return value * n


def _len(value: str) -> int:
    return len(value)


def _make_env() -> Environment:
    env = Environment(loader=BaseLoader())
    env.filters["title_case"]     = _title_case
    env.filters["component_name"] = _component_name
    env.globals["len"]            = _len
    return env


class TemplateGenerator:
    """
    Generates a complete module scaffold from a ModuleSpec.

    Usage:
        spec = ModuleSpec(id="my_module", name="My Module", ...)
        gen  = TemplateGenerator(output_dir=Path("modules/installed"))
        gen.generate(spec)
        # → modules/installed/my_module/ fully scaffolded
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._env = _make_env()

    def generate(self, spec: ModuleSpec) -> Path:
        """
        Render all templates and write the complete module scaffold.

        Returns:
            Path to the created module root directory.
        """
        module_dir = self._output_dir / spec.id
        if module_dir.exists():
            raise FileExistsError(
                f"Module directory already exists: {module_dir}"
            )

        # Create directory structure
        for subdir in ("backend", "frontend", "assets", "docs", "tests"):
            (module_dir / subdir).mkdir(parents=True)
        (module_dir / "docs" / "examples").mkdir()

        # Render and write each file
        ctx = {"spec": spec}

        self._write(module_dir / "manifest.yaml",
                    MANIFEST_TEMPLATE, ctx)

        self._write(module_dir / "backend" / "main.py",
                    BACKEND_MAIN_TEMPLATE, ctx)

        self._write(module_dir / "frontend" / "index.tsx",
                    FRONTEND_TEMPLATE, ctx)

        self._write(module_dir / "docs" / "README.md",
                    README_TEMPLATE, ctx)

        # §16 Documentation First Principle — required so the module
        # passes `techforge validate-module` immediately after creation.
        self._write(module_dir / "docs" / "overview.md",
                    OVERVIEW_TEMPLATE, ctx)
        self._write(module_dir / "docs" / "examples" / "basic.md",
                    BASIC_EXAMPLE_TEMPLATE, ctx)

        self._write(module_dir / "tests" / "test_module.py",
                    TEST_TEMPLATE, ctx)

        # Empty placeholder files
        (module_dir / "assets" / ".gitkeep").touch()

        return module_dir

    def _write(self, path: Path, template_src: str, ctx: dict) -> None:
        tmpl = self._env.from_string(template_src)
        path.write_text(tmpl.render(**ctx), encoding="utf-8")
