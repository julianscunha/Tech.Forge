from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


class Settings(BaseSettings):
    # Platform
    PLATFORM_NAME: str = "TechForge"
    PLATFORM_VERSION: str = "1.0.0"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True

    # Launcher (Phase 6)
    FRONTEND_PORT: int = 5173
    HEALTH_CHECK_TIMEOUT: int = 60      # seconds waiting for backend READY
    FRONTEND_READY_TIMEOUT: int = 60    # seconds waiting for frontend READY

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/config/techforge.db"

    # Frontend static serving — Desktop mode (Fase 6 §10)
    SERVE_STATIC_FRONTEND: bool = False
    FRONTEND_DIST_PATH: Path = BASE_DIR / "core" / "frontend" / "dist"

    # CORS — frontend dev server
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Paths
    MODULES_INSTALLED_PATH: Path = BASE_DIR / "modules" / "installed"
    MODULES_REPOSITORY_PATH: Path = BASE_DIR / "modules" / "repository"
    MODULES_CACHE_PATH: Path = BASE_DIR / "modules" / "cache"
    LOGS_PATH: Path = BASE_DIR / "logs"
    BASE_DIR: Path = BASE_DIR

    model_config = {"env_file": str(BASE_DIR / "config" / ".env"), "extra": "ignore"}


settings = Settings()
