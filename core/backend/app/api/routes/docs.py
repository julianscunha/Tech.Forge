"""
/api/v1/docs — Documentation Engine REST API
=============================================
Exposes the full Documentation Engine to the Developer Center frontend.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional

from app.doc_engine import doc_index, doc_search, doc_indexer
from app.doc_engine.models import DocCategory

router = APIRouter(prefix="/docs", tags=["developer-center"])


# ── Response models ───────────────────────────────────────────────────────────

class DocEntryMeta(BaseModel):
    id:        str
    title:     str
    category:  str
    order:     int
    tags:      list[str]
    excerpt:   str
    module_id: Optional[str]


class DocEntryFull(DocEntryMeta):
    content: str


class SearchResultRead(BaseModel):
    doc_id:    str
    title:     str
    category:  str
    excerpt:   str
    module_id: Optional[str]
    score:     float


class ServiceExportRead(BaseModel):
    name:        str
    description: str
    parameters:  list[dict]
    returns:     Optional[str]
    examples:    list[str]


class ServiceContractRead(BaseModel):
    service_id:   str
    module_id:    str
    description:  str
    version:      str
    exports:      list[ServiceExportRead]
    dependencies: list[str]


class DocSummary(BaseModel):
    total_docs:      int
    total_contracts: int
    categories:      dict[str, int]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=DocSummary)
async def get_doc_summary() -> DocSummary:
    """Overview of all indexed documentation."""
    categories: dict[str, int] = {}
    for entry in doc_index.all():
        key = entry.category.value
        categories[key] = categories.get(key, 0) + 1
    return DocSummary(
        total_docs=doc_index.total,
        total_contracts=len(doc_indexer.all_contracts()),
        categories=categories,
    )


@router.get("/list", response_model=list[DocEntryMeta])
async def list_docs(
    category: Optional[str] = Query(None, description="Filter by DocCategory value"),
    module_id: Optional[str] = Query(None),
) -> list[DocEntryMeta]:
    """List all indexed documentation articles."""
    if module_id:
        entries = doc_index.by_module(module_id)
    elif category:
        try:
            cat = DocCategory(category)
        except ValueError:
            raise HTTPException(400, f"Unknown category: {category!r}")
        entries = doc_index.by_category(cat)
    else:
        entries = sorted(doc_index.all(), key=lambda e: (e.category.value, e.order, e.title))

    return [
        DocEntryMeta(
            id=e.id, title=e.title, category=e.category.value,
            order=e.order, tags=e.tags, excerpt=e.excerpt,
            module_id=e.module_id,
        )
        for e in entries
    ]


@router.get("/article/{doc_id:path}", response_model=DocEntryFull)
async def get_article(doc_id: str) -> DocEntryFull:
    """Return the full content of a single documentation article."""
    entry = doc_index.get(doc_id)
    if not entry:
        raise HTTPException(404, f"Document not found: {doc_id!r}")
    return DocEntryFull(
        id=entry.id, title=entry.title, category=entry.category.value,
        order=entry.order, tags=entry.tags, excerpt=entry.excerpt,
        module_id=entry.module_id, content=entry.content,
    )


@router.get("/search", response_model=list[SearchResultRead])
async def search_docs(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
) -> list[SearchResultRead]:
    """Full-text search across all indexed documentation."""
    results = doc_search.search(q, limit=limit)
    return [
        SearchResultRead(
            doc_id=r.doc_id, title=r.title, category=r.category.value,
            excerpt=r.excerpt, module_id=r.module_id, score=r.score,
        )
        for r in results
    ]


@router.get("/contracts", response_model=list[ServiceContractRead])
async def list_contracts() -> list[ServiceContractRead]:
    """List all service contracts from installed modules."""
    return [_contract_to_read(c) for c in doc_indexer.all_contracts()]


@router.get("/contracts/{module_id}", response_model=ServiceContractRead)
async def get_contract(module_id: str) -> ServiceContractRead:
    """Return the service contract for a specific module."""
    contract = doc_indexer.get_contract(module_id)
    if not contract:
        raise HTTPException(404, f"No service contract found for module: {module_id!r}")
    return _contract_to_read(contract)


@router.post("/reindex", summary="Rebuild the entire documentation index")
async def reindex() -> dict:
    """Rebuild the documentation index from all sources."""
    count = doc_indexer.rebuild()
    return {"indexed": count, "contracts": len(doc_indexer.all_contracts())}


@router.get("/export/ai-context", response_class=PlainTextResponse,
            summary="Export AI context — consolidated Markdown")
async def export_ai_context(
    categories: Optional[str] = Query(
        None,
        description="Comma-separated DocCategory values to include. "
                    "Omit for all.",
    ),
) -> str:
    """
    Generate a single consolidated Markdown document suitable for pasting
    into an AI assistant (Claude, ChatGPT, Gemini) as platform context.
    """
    from app.doc_engine import AIContextExporter
    cat_filter = None
    if categories:
        try:
            cat_filter = [DocCategory(c.strip()) for c in categories.split(",")]
        except ValueError as exc:
            raise HTTPException(400, str(exc))
    return AIContextExporter.export(doc_indexer, cat_filter)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _contract_to_read(c) -> ServiceContractRead:
    return ServiceContractRead(
        service_id=c.service_id,
        module_id=c.module_id,
        description=c.description,
        version=c.version,
        dependencies=c.dependencies,
        exports=[
            ServiceExportRead(
                name=e.name, description=e.description,
                parameters=e.parameters, returns=e.returns,
                examples=e.examples,
            )
            for e in c.exports
        ],
    )


# ── §16 — Documentation First Principle: Completeness ────────────────────────

from app.doc_engine import DocCompletenessChecker
from app.core.settings import settings as _settings


class DoDCheckRead(BaseModel):
    name:     str
    passed:   bool
    required: bool
    detail:   str


class CompletenessReportRead(BaseModel):
    module_id:   str
    module_type: str
    is_complete: bool
    score:       float
    missing:     list[str]
    checks:      list[DoDCheckRead]


def _get_module_type(module_id: str) -> str:
    """Read module_type from manifest.yaml, defaulting to 'application'."""
    import yaml
    manifest_path = _settings.MODULES_INSTALLED_PATH / module_id / "manifest.yaml"
    if not manifest_path.exists():
        return "application"
    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        return str(raw.get("module_type", "application"))
    except Exception as exc:
        logging.getLogger("techforge.docs.api").warning(
            "Failed to read module_type from %s: %s", manifest_path, exc)
        return "application"


@router.get("/completeness", response_model=list[CompletenessReportRead],
            summary="Definition of Done report for all installed modules")
async def get_all_completeness() -> list[CompletenessReportRead]:
    """
    Returns the §16 Definition-of-Done completeness report for every
    installed module: Implementation + Contract + Documentation + Example.
    """
    reports = []
    if not _settings.MODULES_INSTALLED_PATH.exists():
        return reports
    for module_dir in sorted(_settings.MODULES_INSTALLED_PATH.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("."):
            continue
        if not (module_dir / "manifest.yaml").exists():
            continue
        module_type = _get_module_type(module_dir.name)
        report = DocCompletenessChecker.check(module_dir, module_type)
        reports.append(_completeness_to_read(report))
    return reports


@router.get("/completeness/{module_id}", response_model=CompletenessReportRead,
            summary="Definition of Done report for a single module")
async def get_module_completeness(module_id: str) -> CompletenessReportRead:
    """Returns the §16 completeness report for one module."""
    module_dir = _settings.MODULES_INSTALLED_PATH / module_id
    if not module_dir.exists():
        raise HTTPException(404, f"Module not found: {module_id!r}")
    module_type = _get_module_type(module_id)
    report = DocCompletenessChecker.check(module_dir, module_type)
    return _completeness_to_read(report)


def _completeness_to_read(report) -> CompletenessReportRead:
    return CompletenessReportRead(
        module_id=report.module_id,
        module_type=report.module_type,
        is_complete=report.is_complete,
        score=report.score,
        missing=report.missing,
        checks=[
            DoDCheckRead(name=c.name, passed=c.passed, required=c.required, detail=c.detail)
            for c in report.checks
        ],
    )
