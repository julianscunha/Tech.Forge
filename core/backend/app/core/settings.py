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

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/config/techforge.db"

    # CORS — frontend dev server
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Paths
    MODULES_INSTALLED_PATH: Path = BASE_DIR / "modules" / "installed"
    MODULES_REPOSITORY_PATH: Path = BASE_DIR / "modules" / "repository"
    LOGS_PATH: Path = BASE_DIR / "logs"

    model_config = {"env_file": str(BASE_DIR / "config" / ".env"), "extra": "ignore"}


settings = Settings()
