import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.settings import settings
from app.db.database import init_db
from app.doc_engine import doc_indexer
from app.module_engine import journal as loader_journal
from app.module_engine.loader import ModuleLoader
from app.module_engine.plugin_loader import mount_module_routers
from app.observability.logging_setup import configure_logging
from app.observability.notifications_bridge import drain_pending_notifications, wire_notifications
from app.observability.retention import cleanup_old_logs
from app.observability.startup_diagnostics import time_step
from app.runtime import runtime
from app.security.redaction import SecretRedactionFilter

cleanup_old_logs(settings.LOGS_PATH / "backend.jsonl", settings.LOG_RETENTION_DAYS)
configure_logging(level=settings.LOG_LEVEL, logs_path=settings.LOGS_PATH,
                   file_level=settings.LOG_FILE_LEVEL,
                   max_bytes=settings.LOG_MAX_BYTES, backup_count=settings.LOG_BACKUP_COUNT)


def _install_secret_redaction_filter(logger: logging.Logger | None = None) -> None:
    """Fase 12 §28 — filtro no Handler (não no Logger): registros propagados
    de loggers filhos (techforge.module.*) só passam pelos filtros do
    Handler, nunca pelo Logger.filter() de um ancestral."""
    target = logger or logging.getLogger()
    for handler in target.handlers:
        handler.addFilter(SecretRedactionFilter())


_install_secret_redaction_filter()
wire_notifications()

logger = logging.getLogger("techforge.core")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup sequence:
      1. Initialize / migrate database tables
      2. Module Loader — scan installed/ → validate → register
      3. Documentation Indexer — index core docs + installed module docs
    """
    logger.info("TechForge %s starting up…", settings.PLATFORM_VERSION)

    with time_step("database_init"):
        await init_db()
    logger.info("Database initialized.")

    from app.db.database import AsyncSessionLocal
    from app.services.error_registry import ErrorRegistryService
    from app.services.execution_history import ExecutionHistoryService
    with time_step("history_cleanup"):
        async with AsyncSessionLocal() as db:
            removed = await ExecutionHistoryService.cleanup_old(db, settings.EXECUTION_HISTORY_RETENTION_DAYS)
            if removed:
                logger.info("Execution history cleanup: %d old entries removed.", removed)
            removed_errors = await ErrorRegistryService.cleanup_old(db, settings.ERROR_REGISTRY_RETENTION_DAYS)
            if removed_errors:
                logger.info("Error registry cleanup: %d old entries removed.", removed_errors)

    with time_step("module_loader_scan"):
        loader = ModuleLoader()
        result = await loader.scan_installed()
        loader_journal.store(result)
    logger.info(
        "Module Loader: %d installed, %d invalid, %d incompatible.",
        result.installed, result.invalid, result.incompatible,
    )

    # Phase 2+ — Plugin Loader: mount backend routers of INSTALLED modules
    with time_step("plugin_loader_mount"):
        mounted = mount_module_routers(app)
    logger.info(
        "Plugin Loader: %d router(s) mounted, %d failed.",
        len(mounted.mounted), len(mounted.failed),
    )

    # Fase 6 §10 — Desktop mode (no-op se SERVE_STATIC_FRONTEND=false). Montado
    # só agora, DEPOIS do Plugin Loader: o catch-all de SPA casa qualquer
    # caminho, então se viesse antes (como em create_app(), síncrono) ele
    # intercepta toda rota de módulo montada depois — Starlette resolve pela
    # ordem de registro, nunca pela mais específica. Bug real: nenhuma rota
    # de módulo respondia em modo desktop antes desta correção.
    with time_step("static_frontend_mount"):
        _mount_static_frontend(app)

    # Phase 5 — Documentation Engine
    with time_step("doc_indexer"):
        count = doc_indexer.rebuild()
    logger.info("Documentation Engine: %d documents indexed.", count)

    # Fase 4 §21 — sync registry in-memory → DB (dashboard counters)
    from app.db.database import AsyncSessionLocal
    from app.services.registry_sync import sync_registry_to_db
    with time_step("registry_sync_and_integrity"):
        async with AsyncSessionLocal() as db:
            await sync_registry_to_db(db)

            # Fase 10 §15/§28 — verificação de integridade no startup
            # (event-driven, não é polling — roda uma vez, no boot)
            from app.module_engine.enums import ModuleStatus
            from app.module_engine.registry import registry as startup_module_registry
            from app.module_trust.verification import verify_module_integrity
            for entry in startup_module_registry.all():
                if entry.status == ModuleStatus.INSTALLED:
                    try:
                        await verify_module_integrity(entry.module_id, db)
                    except Exception as exc:
                        logger.warning("Startup integrity check failed for %s: %s",
                                       entry.module_id, exc)

    # Fase 8 §26 — Discover Service Modules → Register Services
    from app.service_registry import sync as sync_service_registry
    with time_step("service_registry_sync"):
        await sync_service_registry()

    # Fase 9 §4/§29 — Runtime State reconstruído a partir do Administrative State
    from app.module_engine.registry import registry as module_registry
    from app.module_runtime import module_runtime_registry
    with time_step("runtime_state_rebuild"):
        module_runtime_registry.rebuild(module_registry.all())

    # Phase 6 — Runtime: platform is READY
    await runtime.fire_startup("platform ready")

    yield

    # Fase 8 §27 — stop accepting invocations, clear transient registry state
    from app.service_registry import service_registry
    service_registry.clear_transient_state()

    # Fase 9 §27/§29 — Runtime State é efêmero, nunca sobrevive a um shutdown
    module_runtime_registry.clear_transient_state()

    # Phase 6 — Runtime: coordinated shutdown
    await runtime.fire_shutdown("backend stopped")

    # Fase 17 — espera notificações de segurança agendadas em background
    # terminarem antes do loop fechar (evita task pendente sendo destruída
    # no meio do shutdown).
    await drain_pending_notifications()


def _mount_static_frontend(app: FastAPI) -> bool:
    """
    Desktop mode (Fase 6 §10): serve the compiled frontend from dist/.
    Enabled via SERVE_STATIC_FRONTEND=true + existing dist directory.
    API routes (/api/v1/*) take precedence; unknown non-API paths fall
    back to index.html for SPA routing. Returns True if mounted.
    """
    if not settings.SERVE_STATIC_FRONTEND:
        return False
    dist = settings.FRONTEND_DIST_PATH
    index_html = dist / "index.html"
    if not (dist / "index.html").is_file():
        logger.warning(
            "SERVE_STATIC_FRONTEND is on but %s not found — static UI not served.",
            index_html,
        )
        return False

    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/assets",
        StaticFiles(directory=dist / "assets") if (dist / "assets").is_dir() else StaticFiles(directory=dist),
        name="frontend-assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """SPA fallback: any non-API path serves index.html.

        Só é alcançável de fato por caminhos /api/* que nenhuma rota real
        bateu — este catch-all é montado por último de propósito (ver
        lifespan(), depois de mount_module_routers()), senão ele intercepta
        toda rota de módulo antes dela ser registrada (Starlette casa rotas
        na ordem de registro, não pela mais específica)."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail=f"Not found: /{full_path}")
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_html)

    logger.info("Desktop mode: serving static frontend from %s", dist)
    return True


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PLATFORM_NAME,
        version=settings.PLATFORM_VERSION,
        description="TechForge Core API — modular platform backend",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    return app


app = create_app()
