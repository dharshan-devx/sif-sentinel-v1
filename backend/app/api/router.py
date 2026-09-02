from fastapi import APIRouter

from app.api.routes import analysis, auth, health, models, reports, sites, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(analysis.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(sites.router)
api_router.include_router(reports.router)
api_router.include_router(models.router)
