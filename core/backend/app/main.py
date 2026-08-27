import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.db.database import init_db
from app.api import api_router
from app.module_engine.loader import ModuleLoader
from app.module_engine import journal as loader_journal
from app.module_engine.plugin_loader import mount_module_routers
from app.runtime import runtime
from app.doc_engine import doc_indexer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
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

    await init_db()
    logger.info("Database initialized.")

    loader = ModuleLoader()
    result = await loader.scan_installed()
    loader_journal.store(result)
    logger.info(
        "Module Loader: %d installed, %d invalid, %d incompatible.",
        result.installed, result.invalid, result.incompatible,
    )

    # Phase 2+ — Plugin Loader: mount backend routers of INSTALLED modules
    mounted = mount_module_routers(app)
    logger.info(
        "Plugin Loader: %d router(s) mounted, %d failed.",
        len(mounted.mounted), len(mounted.failed),
    )

    # Phase 5 — Documentation Engine
    count = doc_indexer.rebuild()
    logger.info("Documentation Engine: %d documents indexed.", count)

    # Fase 4 §21 — sync registry in-memory → DB (dashboard counters)
    from app.services.registry_sync import sync_registry_to_db
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await sync_registry_to_db(db)

    # Fase 8 §26 — Discover Service Modules → Register Services
    from app.service_registry import sync as sync_service_registry
    await sync_service_registry()

    # Phase 6 — Runtime: platform is READY
    await runtime.fire_startup("platform ready")

    yield

    # Fase 8 §27 — stop accepting invocations, clear transient registry state
    from app.service_registry import service_registry
    service_registry.clear_transient_state()

    # Phase 6 — Runtime: coordinated shutdown
    await runtime.fire_shutdown("backend stopped")


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
        """SPA fallback: any non-API path serves index.html."""
        if full_path.startswith("api/"):
            raise FileNotFoundError(full_path)
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
    # Fase 6 §10 — Desktop mode (no-op se SERVE_STATIC_FRONTEND=false)
    _mount_static_frontend(app)
    return app


app = create_app()
