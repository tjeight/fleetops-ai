import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    JSON,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class IncidentModel(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"inc-{uuid.uuid4().hex[:8]}")
    site_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    drone_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM", index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True, index=True)
    
    # Operational Evidence Snapshots
    telemetry_snapshot: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    mission_history: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    device_health: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    investigations: Mapped[List["InvestigationModel"]] = relationship(
        "InvestigationModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin", order_by="InvestigationModel.created_at.desc()"
    )
    policy_decisions: Mapped[List["PolicyDecisionModel"]] = relationship(
        "PolicyDecisionModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    approval_requests: Mapped[List["ApprovalRequestModel"]] = relationship(
        "ApprovalRequestModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    simulated_actions: Mapped[List["SimulatedActionModel"]] = relationship(
        "SimulatedActionModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin"
    )
    audit_events: Mapped[List["AuditEventModel"]] = relationship(
        "AuditEventModel", back_populates="incident", cascade="all, delete-orphan", lazy="selectin", order_by="AuditEventModel.timestamp.asc()"
    )


class InvestigationModel(Base):
    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="COMPLETED")
    
    likely_cause: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis_category: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_facts: Mapped[List[str]] = mapped_column(JSON, default=list)
    hypotheses: Mapped[List[str]] = mapped_column(JSON, default=list)
    uncertainty_notes: Mapped[str] = mapped_column(Text, default="")
    
    # Retrieved citations from ChromaDB
    retrieved_sop_citations: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    
    # Recommended Response
    recommended_action: Mapped[str] = mapped_column(String(64), nullable=False)
    recommended_action_params: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    preconditions: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="investigations")


class PolicyDecisionModel(Base):
    __tablename__ = "policy_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    investigation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)  # ALLOW, BLOCK, REQUIRES_APPROVAL, INSUFFICIENT_EVIDENCE
    reasons: Mapped[List[str]] = mapped_column(JSON, default=list)
    failed_checks: Mapped[List[str]] = mapped_column(JSON, default=list)
    policy_ids_evaluated: Mapped[List[str]] = mapped_column(JSON, default=list)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="policy_decisions")


class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action_params: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    operator_role: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="approval_requests")


class SimulatedActionModel(Base):
    __tablename__ = "simulated_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action_params: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="EXECUTED")  # EXECUTED, BLOCKED, FAILED
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    mock_result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="simulated_actions")


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)

    incident: Mapped["IncidentModel"] = relationship("IncidentModel", back_populates="audit_events")
