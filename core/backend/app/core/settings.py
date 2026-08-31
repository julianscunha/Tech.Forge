from pathlib import Path

from pydantic_settings import BaseSettings

from app.core.paths import ensure_user_data_dirs, install_dir, user_data_dir

BASE_DIR = install_dir()
USER_DATA_DIR = user_data_dir()
ensure_user_data_dirs(USER_DATA_DIR)


class Settings(BaseSettings):
    # Platform
    PLATFORM_NAME: str = "TechForge"
    PLATFORM_VERSION: str = "1.0.0"

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True

    # Observability (Fase 14)
    LOG_LEVEL: str = "INFO"
    LOG_FILE_LEVEL: str | None = None   # None = mesmo nível de LOG_LEVEL
    LOG_MAX_BYTES: int = 10_000_000     # 10MB — limite de tamanho do backend.jsonl antes de rotacionar
    LOG_BACKUP_COUNT: int = 5
    LOG_RETENTION_DAYS: dict[str, int] = {
        "DEBUG": 7, "INFO": 30, "WARNING": 30, "ERROR": 90, "CRITICAL": 90,
    }
    EXECUTION_HISTORY_RETENTION_DAYS: int = 90
    ERROR_REGISTRY_RETENTION_DAYS: int = 90

    # Launcher (Phase 6)
    FRONTEND_PORT: int = 5173
    HEALTH_CHECK_TIMEOUT: int = 60      # seconds waiting for backend READY
    FRONTEND_READY_TIMEOUT: int = 60    # seconds waiting for frontend READY

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{USER_DATA_DIR}/config/techforge.db"

    # Frontend static serving — Desktop mode (Fase 6 §10)
    SERVE_STATIC_FRONTEND: bool = False
    FRONTEND_DIST_PATH: Path = BASE_DIR / "core" / "frontend" / "dist"

    # CORS — frontend dev server
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Official module catalog (Fase 11) — index.json + .mod built by CI in
    # julianscunha/Tech.Forge.Modules, committed under modules/ on main.
    OFFICIAL_CATALOG_BASE_URL: str = (
        "https://raw.githubusercontent.com/julianscunha/Tech.Forge.Modules/main/modules"
    )

    # Paths — dados do usuário (Fase 16 §11/§12/§13): DB, módulos, logs.
    # Coincide com BASE_DIR em árvore de desenvolvimento; em produção
    # instalada, resolve para o diretório de dados do SO (app/core/paths.py).
    MODULES_INSTALLED_PATH: Path = USER_DATA_DIR / "modules" / "installed"
    MODULES_REPOSITORY_PATH: Path = USER_DATA_DIR / "modules" / "repository"
    MODULES_CACHE_PATH: Path = USER_DATA_DIR / "modules" / "cache"
    LOGS_PATH: Path = USER_DATA_DIR / "logs"
    BASE_DIR: Path = BASE_DIR
    USER_DATA_DIR: Path = USER_DATA_DIR

    model_config = {"env_file": str(USER_DATA_DIR / "config" / ".env"), "extra": "ignore"}


settings = Settings()
