import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.db.database import init_db
from app.api import api_router
from app.module_engine.loader import ModuleLoader
from app.module_engine import journal as loader_journal

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
      2. Run Module Loader — scan installed/ → validate → register
      3. Store loader journal for Developer Mode
    """
    logger.info("TechForge %s starting up…", settings.PLATFORM_VERSION)

    # Step 1 — DB
    await init_db()
    logger.info("Database initialized.")

    # Step 2 — Module Loader (Phase 2)
    loader = ModuleLoader()
    result = await loader.scan_installed()

    # Step 3 — preserve journal for /api/v1/registry/loader/journal
    loader_journal.store(result)
    logger.info(
        "Module Loader finished: %d installed, %d invalid, %d incompatible.",
        result.installed, result.invalid, result.incompatible,
    )

    yield
    # Shutdown — nothing to teardown for SQLite / in-memory registry


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
