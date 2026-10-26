from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.incidents import router as incidents_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.dashboard import router as dashboard_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(incidents_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(dashboard_router)
