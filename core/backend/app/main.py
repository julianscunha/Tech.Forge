import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.db.database import init_db
from app.api import api_router
from app.module_engine.loader import ModuleLoader
from app.module_engine import journal as loader_journal
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

    # Phase 5 — Documentation Engine
    count = doc_indexer.rebuild()
    logger.info("Documentation Engine: %d documents indexed.", count)

    yield


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
