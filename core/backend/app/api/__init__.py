from fastapi import APIRouter
from app.api.routes.platform  import router as platform_router
from app.api.routes.categories import router as categories_router
from app.api.routes.modules    import router as modules_router
from app.api.routes.registry   import router as registry_router
from app.api.routes.health     import router as health_router

# Central v1 router
# Phase 3 additions: marketplace_router, sdk_router
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(platform_router)
api_router.include_router(categories_router)
api_router.include_router(modules_router)
api_router.include_router(registry_router)   # Phase 2 — runtime registry
api_router.include_router(health_router)     # Phase 2 — health checks
