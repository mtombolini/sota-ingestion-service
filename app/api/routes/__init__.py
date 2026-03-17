"""API route modules — assembled into a single router for the app."""

from fastapi import APIRouter

from app.api.routes.tenants import router as tenants_router
from app.api.routes.connectors import router as connectors_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.data import router as data_router
from app.api.routes.legacy_bsale import router as legacy_bsale_router

admin_router = APIRouter(prefix="/admin", tags=["admin"])
admin_router.include_router(tenants_router)
admin_router.include_router(connectors_router)
admin_router.include_router(jobs_router)
admin_router.include_router(data_router)

router = APIRouter()
router.include_router(admin_router)
router.include_router(legacy_bsale_router)
