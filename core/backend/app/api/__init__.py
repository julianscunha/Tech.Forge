from fastapi import APIRouter
from app.api.routes.platform    import router as platform_router
from app.api.routes.categories  import router as categories_router
from app.api.routes.modules     import router as modules_router
from app.api.routes.registry    import router as registry_router
from app.api.routes.health      import router as health_router
from app.api.routes.marketplace import router as marketplace_router
from app.api.routes.docs        import router as docs_router
from app.runtime.routes         import router as runtime_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.module_assets import router as module_assets_router
from app.api.routes.docs_context import router as docs_context_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(platform_router)
api_router.include_router(categories_router)
api_router.include_router(modules_router)
api_router.include_router(registry_router)     # Phase 2
api_router.include_router(health_router)       # Phase 2
api_router.include_router(marketplace_router)  # Phase 4
api_router.include_router(docs_router)         # Phase 5
api_router.include_router(runtime_router)      # Phase 6
api_router.include_router(notifications_router)  # Phase 2 — Notification Foundation
api_router.include_router(module_assets_router)  # Phase 3 — module frontend assets
api_router.include_router(docs_context_router)   # Fase 5 — help contextual
