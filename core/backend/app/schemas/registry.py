from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ── Category ─────────────────────────────────────────────────────────────────

class CategoryBase(BaseModel):
    slug: str
    name: str
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
    module_id: str
    name: str
    version: str
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
