from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.db.database import init_db
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: initialize DB tables
    await init_db()
    yield
    # Shutdown: nothing to teardown for SQLite


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PLATFORM_NAME,
        version=settings.PLATFORM_VERSION,
        description="TechForge Core API — modular platform backend",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )

    # CORS — allow frontend dev server and future server deployments
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
