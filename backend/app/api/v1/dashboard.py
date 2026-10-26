from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.incident import DashboardStats
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_statistics(db: AsyncSession = Depends(get_db)):
    """
    Get live aggregated incident metrics and simulated fleet health roster.
    All metrics derive from the database.
    """
    return await IncidentService.get_dashboard_stats(db)
