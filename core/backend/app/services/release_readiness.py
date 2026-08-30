"""Fase 15 §36/§37 — Release Readiness Report.

Agrega os validadores já existentes (Fases 7, 12) num único relatório
READY/BLOCKED. Reusa os serviços — não recalcula nada em paralelo (spec §2:
"não criar critérios paralelos de qualidade").

Tests e Build ficam FORA deste agregador de propósito: rodar a suíte
pytest inteira (~70s) ou `npm run build` dentro do processo do próprio
servidor que está sendo avaliado é pesado e circular. `techforge
release-check` (CLI) roda os dois via subprocess e soma ao relatório desta
função — a API (`GET /api/v1/release/readiness`) expõe só o subconjunto
computável ao vivo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.migrations import head_revision
from app.db.storage import storage_provider
from app.doc_engine.completeness import DocCompletenessChecker
from app.module_engine.enums import ModuleStatus
from app.module_engine.registry import registry
from app.services.changelog import parse_changelog, validate_changelog
from app.services.versioning import is_valid_semver


@dataclass
class ReleaseCheck:
    name: str
    passed: bool
    detail: str


@dataclass
class ReleaseReadinessReport:
    version: str
    checks: list[ReleaseCheck] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return all(c.passed for c in self.checks)


def _check_version_consistency() -> ReleaseCheck:
    version = settings.PLATFORM_VERSION
    if not is_valid_semver(version):
        return ReleaseCheck("version_consistency", False, f"PLATFORM_VERSION '{version}' não é SemVer válido")
    return ReleaseCheck("version_consistency", True, f"PLATFORM_VERSION={version}")


def _check_documentation() -> ReleaseCheck:
    # Só módulos validamente instalados — INVALID/INCOMPATIBLE já são
    # bloqueados por outro gate (validação de manifest), não faz sentido
    # cobrar documentação de um módulo que nem carrega.
    valid_entries = [e for e in registry.all() if e.status in (ModuleStatus.INSTALLED, ModuleStatus.DISABLED)]
    incomplete = []
    for entry in valid_entries:
        module_path = settings.MODULES_INSTALLED_PATH / entry.module_id
        module_type = (entry.manifest_raw or {}).get("module_type", "application")
        report = DocCompletenessChecker.check(module_path, module_type)
        if not report.is_complete:
            incomplete.append(entry.module_id)
    if incomplete:
        return ReleaseCheck("documentation", False, f"Módulos incompletos: {incomplete}")
    return ReleaseCheck("documentation", True, f"{len(valid_entries)} módulo(s) — documentação completa")


async def _check_migrations(db: AsyncSession) -> ReleaseCheck:
    from sqlalchemy import text

    head = head_revision()
    try:
        result = await db.execute(text("SELECT version_num FROM alembic_version"))
        row = result.first()
        current = row[0] if row else None
    except Exception:
        current = None

    if current != head:
        return ReleaseCheck("migrations", False, f"current={current} head={head}")
    return ReleaseCheck("migrations", True, f"head={head}")


async def _check_storage(db: AsyncSession) -> ReleaseCheck:
    health = await storage_provider.health_check(db)
    if not (health.database and health.writable):
        return ReleaseCheck("storage", False, "banco indisponível ou não-gravável")
    return ReleaseCheck("storage", True, "banco disponível e gravável")


def _check_changelog() -> ReleaseCheck:
    changelog_file = settings.BASE_DIR / "CHANGELOG.md"
    if not changelog_file.exists():
        return ReleaseCheck("changelog", False, "CHANGELOG.md não encontrado")
    text = changelog_file.read_text(encoding="utf-8")
    errors = validate_changelog(text)
    if errors:
        return ReleaseCheck("changelog", False, "; ".join(errors))
    entries = parse_changelog(text)
    has_current = any(e.version == settings.PLATFORM_VERSION for e in entries)
    if not has_current:
        return ReleaseCheck(
            "changelog", False, f"Nenhuma entrada para a versão atual ({settings.PLATFORM_VERSION})"
        )
    return ReleaseCheck("changelog", True, "formato válido, versão atual documentada")


async def compute_release_readiness(db: AsyncSession) -> ReleaseReadinessReport:
    report = ReleaseReadinessReport(version=settings.PLATFORM_VERSION)
    report.checks.append(_check_version_consistency())
    report.checks.append(_check_changelog())
    report.checks.append(_check_documentation())
    report.checks.append(await _check_migrations(db))
    report.checks.append(await _check_storage(db))
    return report
