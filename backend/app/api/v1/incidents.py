from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentSummary,
    InvestigationResponse,
    PolicyDecisionResponse,
    ApprovalResponse,
    SimulatedActionResponse,
    AuditEventResponse
)
from app.schemas.approval import ApprovalDecisionRequest
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(data: IncidentCreate, db: AsyncSession = Depends(get_db)):
    """
    Intake a new simulated drone incident.
    Idempotent: repeating with the same idempotency_key returns the existing incident.
    """
    return await IncidentService.create_incident(data, db)


@router.get("", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status (OPEN, INVESTIGATING, AWAITING_APPROVAL, RESOLVED, BLOCKED)"),
    severity: Optional[str] = Query(None, description="Filter by severity (LOW, MEDIUM, HIGH, CRITICAL)"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List incidents with optional status and severity filtering.
    """
    return await IncidentService.list_incidents(db, status_filter=status, severity_filter=severity, limit=limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve full incident details including investigations, policy decisions, approvals, and audit trail.
    """
    return await IncidentService.get_incident(incident_id, db)


@router.post("/{incident_id}/investigate", response_model=IncidentResponse)
async def trigger_investigation(
    incident_id: str,
    simulate_timeout: bool = Query(False, description="Simulate a tool execution timeout for test verification"),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute stateful LangGraph investigation workflow for the incident.
    """
    return await IncidentService.run_investigation(incident_id, db, simulate_timeout=simulate_timeout)


@router.post("/{incident_id}/approval", response_model=IncidentResponse)
async def resolve_approval(
    incident_id: str,
    data: ApprovalDecisionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a pending simulated flight action.
    Enforces authorization check and deterministic policy revalidation.
    """
    return await IncidentService.resolve_approval(
        incident_id=incident_id,
        decision=data.decision,
        operator_role=data.operator_role,
        operator_id=data.operator_id,
        rejection_reason=data.rejection_reason,
        db=db
    )


@router.get("/{incident_id}/investigations", response_model=List[InvestigationResponse])
async def get_investigations(incident_id: str, db: AsyncSession = Depends(get_db)):
    """
    View investigation results and evidence for a specific incident.
    """
    incident = await IncidentService.get_incident(incident_id, db)
    return incident.investigations


@router.get("/{incident_id}/audit", response_model=List[AuditEventResponse])
async def get_audit_events(incident_id: str, db: AsyncSession = Depends(get_db)):
    """
    Chronological append-only audit trail for the incident.
    """
    incident = await IncidentService.get_incident(incident_id, db)
    return incident.audit_events


@router.get("/{incident_id}/actions", response_model=List[SimulatedActionResponse])
async def get_simulated_actions(incident_id: str, db: AsyncSession = Depends(get_db)):
    """
    View simulated action execution history and mock telemetry acknowledgment.
    """
    incident = await IncidentService.get_incident(incident_id, db)
    return incident.simulated_actions
