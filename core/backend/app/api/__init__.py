from fastapi import APIRouter
from app.api.routes.platform import router as platform_router
from app.api.routes.categories import router as categories_router
from app.api.routes.modules import router as modules_router

# Central router — all v1 endpoints
# Future routers (marketplace, sdk, health-checks) are added here
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(platform_router)
api_router.include_router(categories_router)
api_router.include_router(modules_router)
