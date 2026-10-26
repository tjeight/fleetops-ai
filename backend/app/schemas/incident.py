from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TelemetrySnapshot(BaseSchema):
    battery_pct: float = Field(..., description="Battery level 0-100%")
    altitude_m: float = Field(0.0, description="Altitude in meters")
    speed_mps: float = Field(0.0, description="Current speed in m/s")
    gps_lat: float = Field(..., description="Latitude")
    gps_lon: float = Field(..., description="Longitude")
    heading_deg: float = Field(0.0, description="Heading in degrees")
    timestamp: datetime = Field(..., description="Telemetry timestamp")
    signal_strength_dbm: float = Field(-65.0, description="Signal strength")
    heartbeat_ok: bool = Field(True, description="Heartbeat status")


class IncidentCreate(BaseSchema):
    site_id: str = Field(..., description="Site identifier")
    drone_id: str = Field(..., description="Drone identifier")
    event_type: str = Field(..., description="Event type")
    severity: str = Field("MEDIUM", description="Severity level")
    idempotency_key: Optional[str] = Field(None, description="Optional idempotency key")
    telemetry_snapshot: Dict[str, Any] = Field(default_factory=dict)
    mission_history: Dict[str, Any] = Field(default_factory=dict)
    device_health: Dict[str, Any] = Field(default_factory=dict)


class SOPCitation(BaseSchema):
    sop_id: str
    title: str
    section: Optional[str] = None
    excerpt: str
    relevance_score: float = 0.0


class InvestigationResponse(BaseSchema):
    id: str
    incident_id: str
    status: str
    likely_cause: str
    diagnosis_category: str
    observed_facts: List[str]
    hypotheses: List[str]
    uncertainty_notes: str
    retrieved_sop_citations: List[Dict[str, Any]]
    recommended_action: str
    recommended_action_params: Dict[str, Any]
    preconditions: List[str]
    created_at: datetime


class PolicyDecisionResponse(BaseSchema):
    id: str
    incident_id: str
    investigation_id: Optional[str] = None
    action_type: str
    outcome: str
    reasons: List[str]
    failed_checks: List[str]
    policy_ids_evaluated: List[str]
    evaluated_at: datetime


class ApprovalResponse(BaseSchema):
    id: str
    incident_id: str
    action_type: str
    action_params: Dict[str, Any]
    status: str
    requested_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    operator_role: Optional[str] = None
    rejection_reason: Optional[str] = None


class SimulatedActionResponse(BaseSchema):
    id: str
    incident_id: str
    action_type: str
    action_params: Dict[str, Any]
    idempotency_key: str
    status: str
    executed_at: datetime
    mock_result: Dict[str, Any]


class AuditEventResponse(BaseSchema):
    id: str
    incident_id: str
    actor: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime


class IncidentResponse(BaseSchema):
    id: str
    site_id: str
    drone_id: str
    event_type: str
    severity: str
    status: str
    idempotency_key: Optional[str] = None
    telemetry_snapshot: Dict[str, Any]
    mission_history: Dict[str, Any]
    device_health: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    investigations: List[InvestigationResponse] = []
    policy_decisions: List[PolicyDecisionResponse] = []
    approval_requests: List[ApprovalResponse] = []
    simulated_actions: List[SimulatedActionResponse] = []
    audit_events: List[AuditEventResponse] = []


class IncidentSummary(BaseSchema):
    id: str
    site_id: str
    drone_id: str
    event_type: str
    severity: str
    status: str
    policy_outcome: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DroneHealth(BaseSchema):
    drone_id: str
    site_id: str
    status: str
    battery_pct: float
    last_seen: datetime


class DashboardStats(BaseSchema):
    total_incidents: int
    open_incidents: int
    investigating_incidents: int
    awaiting_approval_incidents: int
    resolved_incidents: int
    blocked_incidents: int
    fleet_health: List[DroneHealth]
