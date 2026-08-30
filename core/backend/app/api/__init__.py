from fastapi import APIRouter

from app.api.routes.catalog import router as catalog_router
from app.api.routes.categories import router as categories_router
from app.api.routes.dependencies import dependencies_router
from app.api.routes.dependencies import modules_router as dependencies_modules_router
from app.api.routes.docs import router as docs_router
from app.api.routes.docs_context import router as docs_context_router
from app.api.routes.health import router as health_router
from app.api.routes.marketplace import router as marketplace_router
from app.api.routes.module_assets import router as module_assets_router
from app.api.routes.module_config import router as module_config_router
from app.api.routes.module_verification import router as module_verification_router
from app.api.routes.modules import router as modules_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.platform import router as platform_router
from app.api.routes.platform_config import router as platform_config_router
from app.api.routes.publishers import router as publishers_router
from app.api.routes.registry import router as registry_router
from app.api.routes.release import router as release_router
from app.api.routes.services import router as services_router
from app.api.routes.system import router as system_router
from app.runtime.routes import router as runtime_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(platform_router)
api_router.include_router(categories_router)
# Fase 10: module_verification_router precisa vir ANTES de modules_router —
# GET /modules/trust colide com a rota generica GET /modules/{module_id}
# (modules.py), que casaria "trust" como module_id se registrada primeiro.
api_router.include_router(module_verification_router)  # Fase 10 — Runtime Integrity Verification
api_router.include_router(modules_router)
api_router.include_router(registry_router)     # Phase 2
api_router.include_router(health_router)       # Phase 2
api_router.include_router(marketplace_router)  # Phase 4
api_router.include_router(docs_router)         # Phase 5
api_router.include_router(runtime_router)      # Phase 6
api_router.include_router(notifications_router)  # Phase 2 — Notification Foundation
api_router.include_router(module_assets_router)  # Phase 3 — module frontend assets
api_router.include_router(docs_context_router)   # Fase 5 — help contextual
api_router.include_router(services_router)       # Fase 8 — Service Registry
api_router.include_router(dependencies_modules_router)  # Fase 8.1 — Dependency Governance
api_router.include_router(dependencies_router)          # Fase 8.1 — Dependency Governance
api_router.include_router(publishers_router)           # Fase 10 — Publisher Registry
api_router.include_router(catalog_router)              # Fase 11 — Module Catalog
api_router.include_router(system_router)               # Fase 12 — Storage & Persistence
api_router.include_router(module_config_router)         # Fase 12 — Module Configuration
api_router.include_router(platform_config_router)       # Fase 12 — Platform Configuration (GET /config)
api_router.include_router(release_router)               # Fase 15 — Release Readiness Report
