from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Category(Base):
    """
    Represents a module category (e.g. Backup, Virtualization, Cloud).
    Categories are registered by the Core and discovered automatically
    from installed module manifests.
    """
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationship — will be used by Plugin Loader in Phase 2
    modules: Mapped[list["Module"]] = relationship("Module", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category slug={self.slug!r}>"


class Module(Base):
    """
    Registry entry for an installed module.
    This table is the integration point for the Plugin Loader (Phase 2).
    Each row corresponds to a module directory under modules/installed/.
    """
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    module_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vendor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Version constraints — enforced by Marketplace / compatibility checker (Phase 5)
    platform_min_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    platform_max_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Entry points — used by Plugin Loader (Phase 2)
    entry_backend: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    entry_frontend: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Security fields — enforced in Phase 5
    signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Lifecycle state
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now(), nullable=True)

    # FK → Category
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("categories.id"), nullable=True)
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="modules")

    def __repr__(self) -> str:
        return f"<Module id={self.module_id!r} version={self.version!r}>"
