from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.scenario import ScenarioItem, ScenarioRunRequest
from app.schemas.incident import IncidentCreate, IncidentResponse
from app.services.scenario_catalog import get_seeded_scenarios, get_scenario_by_id
from app.services.incident_service import IncidentService

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("", response_model=List[ScenarioItem])
async def list_scenarios():
    """
    List all predefined repeatable evaluation scenarios.
    """
    return get_seeded_scenarios()


@router.post("/run")
async def run_scenario(request: ScenarioRunRequest, db: AsyncSession = Depends(get_db)):
    """
    Execute a predefined scenario end-to-end.
    Creates incident, triggers investigation, and tests policy / mock action boundaries.
    """
    scenario = get_scenario_by_id(request.scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{request.scenario_id}' not found in catalog"
        )

    # 1. Create Incident from Scenario Payload
    payload = scenario["payload"]
    incident_in = IncidentCreate(**payload)
    
    # Check for duplicate scenario (Scenario 3 tests idempotency)
    incident = await IncidentService.create_incident(incident_in, db)

    # Special handling for scenarios
    simulate_timeout = (request.scenario_id == "tool_timeout")
    
    # 2. Run LangGraph Investigation
    incident = await IncidentService.run_investigation(
        incident_id=incident.id,
        db=db,
        simulate_timeout=simulate_timeout
    )

    # 3. Special scenario step: Unauthorized Operator (Scenario 6)
    auth_test_passed = False
    auth_error_message = None
    if request.scenario_id == "unauthorized_operator":
        try:
            # Attempt approval with 'viewer' role
            await IncidentService.resolve_approval(
                incident_id=incident.id,
                decision="APPROVE",
                operator_role="viewer",
                operator_id="operator-viewer",
                rejection_reason=None,
                db=db
            )
        except HTTPException as e:
            if e.status_code == 403:
                auth_test_passed = True
                auth_error_message = e.detail

    # Refresh incident state
    incident = await IncidentService.get_incident(incident.id, db)
    
    latest_pol = incident.policy_decisions[0].outcome if incident.policy_decisions else "UNKNOWN"
    
    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "expected_outcome": scenario["expected_outcome"],
        "actual_status": incident.status,
        "expected_policy_decision": scenario["expected_policy_decision"],
        "actual_policy_decision": latest_pol,
        "matches_expected": (
            (request.scenario_id == "unauthorized_operator" and auth_test_passed) or
            (incident.status == scenario["expected_outcome"])
        ),
        "unauthorized_auth_blocked": auth_test_passed if request.scenario_id == "unauthorized_operator" else None,
        "auth_error_detail": auth_error_message,
        "incident": IncidentResponse.model_validate(incident)
    }
