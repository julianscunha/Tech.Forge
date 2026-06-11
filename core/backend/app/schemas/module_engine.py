from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.module_engine.enums import ModuleStatus


class ModuleEntryRead(BaseModel):
    """Runtime representation of a registered module (from in-memory registry)."""
    model_config = ConfigDict(from_attributes=True)

    module_id:   str
    name:        str
    version:     str
    category:    str
    vendor:      str
    author:      str
    description: str
    status:      ModuleStatus
    install_date: datetime
    errors:      list[str]
    warnings:    list[str]
    platform_min_version: str
    platform_max_version: str
    entry_backend:  Optional[str]
    entry_frontend: Optional[str]
    is_active:   bool

    # UI display fields
    icon:  Optional[str] = None
    color: Optional[str] = None
    order: Optional[int] = None

    # Only present when Developer Mode is enabled
    manifest_raw: Optional[dict] = None


class LoadEventRead(BaseModel):
    timestamp: datetime
    module_id: Optional[str]
    level:     str
    message:   str
    details:   dict


class LoaderResultRead(BaseModel):
    scanned:      int
    installed:    int
    disabled:     int
    invalid:      int
    incompatible: int
    journal:      list[LoadEventRead]


class RegistrySummary(BaseModel):
    total:       int
    installed:   int
    disabled:    int
    invalid:     int
    categories:  list[str]
