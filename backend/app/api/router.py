from fastapi import APIRouter

from app.api.routes import (
    analysis,
    auth,
    dashboard,
    health,
    models,
    precursors,
    reports,
    reviews,
    risk,
    rules,
    sites,
    users,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(analysis.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(sites.router)
api_router.include_router(reports.router)
api_router.include_router(models.router)
api_router.include_router(precursors.router)
api_router.include_router(risk.router)
api_router.include_router(dashboard.router)
api_router.include_router(reviews.router)
api_router.include_router(rules.router)
