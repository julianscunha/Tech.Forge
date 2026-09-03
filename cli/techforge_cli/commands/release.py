"""techforge release-check — Release Readiness Report (Fase 15 §36/§37/§46).

Combina o subconjunto computável ao vivo (via HTTP, GET /api/v1/release/readiness
— módulo/docs/migrations/storage/changelog/versão) com Tests e Build, que
este comando roda via subprocess (pytest e npm run build), porque rodá-los
de dentro do próprio processo do servidor avaliado seria pesado e circular.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from techforge_cli.console import console, print_error, print_info
from techforge_cli.http import core_get

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _get_readiness() -> dict | None:
    return core_get("/release/readiness", timeout=30)


def _run_backend_tests() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q"],
        cwd=_REPO_ROOT / "core" / "backend",
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _run_frontend_build() -> bool:
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=_REPO_ROOT / "core" / "frontend",
        capture_output=True,
        text=True,
        shell=(sys.platform == "win32"),
    )
    return result.returncode == 0


@click.command("release-check")
@click.option("--skip-tests", is_flag=True, help="Pula a suíte pytest (mais rápido, menos completo).")
@click.option("--skip-build", is_flag=True, help="Pula o build do frontend.")
def release_check_cmd(skip_tests: bool, skip_build: bool):
    """Run the full Release Readiness Report (live checks + tests + build)."""
    readiness = _get_readiness()
    if readiness is None:
        raise SystemExit(1)

    console.print(f"Version: {readiness['version']}\n")
    all_passed = readiness["ready"]
    for check in readiness["checks"]:
        mark = "PASS" if check["passed"] else "FAIL"
        console.print(f"{check['name']}: {mark} — {check['detail']}")

    if not skip_tests:
        tests_ok = _run_backend_tests()
        console.print(f"tests: {'PASS' if tests_ok else 'FAIL'}")
        all_passed = all_passed and tests_ok
    else:
        console.print("tests: SKIPPED")

    if not skip_build:
        build_ok = _run_frontend_build()
        console.print(f"build: {'PASS' if build_ok else 'FAIL'}")
        all_passed = all_passed and build_ok
    else:
        console.print("build: SKIPPED")

    console.print()
    if all_passed:
        print_info("Release: READY")
    else:
        print_error("Release: BLOCKED")
        raise SystemExit(1)
