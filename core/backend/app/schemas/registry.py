import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

_MODULE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _check_module_id(v: str) -> str:
    if not _MODULE_ID_RE.match(v):
        raise ValueError("module_id must be snake_case (lowercase letters, digits, underscores)")
    return v


def _check_semver(v: str) -> str:
    if not _SEMVER_RE.match(v):
        raise ValueError("version must follow semver format X.Y.Z")
    return v


# ── Platform health (Fase 1 spec §5) ─────────────────────────────────────────

class PlatformHealthCheck(BaseModel):
    status: str
    platform: str
    version: str
    database: str


# ── Category ─────────────────────────────────────────────────────────────────

class CategoryBase(BaseModel):
    slug: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: Optional[str] = None
    icon: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ── Module ────────────────────────────────────────────────────────────────────

class ModuleBase(BaseModel):
    module_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: Optional[str] = None
    vendor: Optional[str] = None
    author: Optional[str] = None
    platform_min_version: Optional[str] = None
    platform_max_version: Optional[str] = None
    entry_backend: Optional[str] = None
    entry_frontend: Optional[str] = None
    is_enabled: bool = True
    category_id: Optional[int] = None


class ModuleCreate(ModuleBase):
    pass


class ModuleRead(ModuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    installed_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[CategoryRead] = None


# ── Platform Status ───────────────────────────────────────────────────────────

class PlatformStatus(BaseModel):
    platform_name: str
    platform_version: str
    backend_status: str          # "online" | "degraded" | "offline"
    database_status: str         # "connected" | "error"
    modules_installed: int
    modules_enabled: int
    categories_registered: int
    safe_mode: bool = False      # Fase 16 §16/§18
