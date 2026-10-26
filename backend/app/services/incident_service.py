import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.entities import (
    IncidentModel,
    InvestigationModel,
    PolicyDecisionModel,
    ApprovalRequestModel,
    SimulatedActionModel,
    AuditEventModel,
    get_utc_now
)
from app.schemas.incident import IncidentCreate
from app.agents.investigation_graph import investigation_graph
from app.policies.rules import evaluate_safety_policy
from app.tools.mock_action_api import mock_action_api
from app.core.config import settings


class IncidentService:
    @staticmethod
    async def create_incident(data: IncidentCreate, db: AsyncSession) -> IncidentModel:
        # 1. Idempotency Check
        if data.idempotency_key:
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.idempotency_key == data.idempotency_key)
                .options(
                    selectinload(IncidentModel.investigations),
                    selectinload(IncidentModel.policy_decisions),
                    selectinload(IncidentModel.approval_requests),
                    selectinload(IncidentModel.simulated_actions),
                    selectinload(IncidentModel.audit_events)
                )
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                return existing

        incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        incident = IncidentModel(
            id=incident_id,
            site_id=data.site_id,
            drone_id=data.drone_id,
            event_type=data.event_type,
            severity=data.severity,
            status="OPEN",
            idempotency_key=data.idempotency_key,
            telemetry_snapshot=data.telemetry_snapshot,
            mission_history=data.mission_history,
            device_health=data.device_health,
        )
        db.add(incident)
        
        # Initial Audit Event
        audit = AuditEventModel(
            incident_id=incident_id,
            actor="system:api_gateway",
            event_type="INCIDENT_CREATED",
            payload={
                "event_type": data.event_type,
                "severity": data.severity,
                "site_id": data.site_id,
                "drone_id": data.drone_id,
                "idempotency_key": data.idempotency_key
            }
        )
        db.add(audit)
        
        incident.investigations = []
        incident.policy_decisions = []
        incident.approval_requests = []
        incident.simulated_actions = []
        incident.audit_events = [audit]
        await db.commit()
        
        return incident

    @staticmethod
    async def get_incident(incident_id: str, db: AsyncSession) -> IncidentModel:
        stmt = (
            select(IncidentModel)
            .where(IncidentModel.id == incident_id)
            .options(
                selectinload(IncidentModel.investigations),
                selectinload(IncidentModel.policy_decisions),
                selectinload(IncidentModel.approval_requests),
                selectinload(IncidentModel.simulated_actions),
                selectinload(IncidentModel.audit_events)
            )
        )
        result = await db.execute(stmt)
        incident = result.scalar_one_or_none()
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident {incident_id} not found")
        return incident

    @staticmethod
    async def run_investigation(
        incident_id: str,
        db: AsyncSession,
        simulate_timeout: bool = False
    ) -> IncidentModel:
        incident = await IncidentService.get_incident(incident_id, db)
        
        initial_state = {
            "incident_id": incident.id,
            "site_id": incident.site_id,
            "drone_id": incident.drone_id,
            "event_type": incident.event_type,
            "severity": incident.severity,
            "telemetry_snapshot": incident.telemetry_snapshot,
            "mission_history": incident.mission_history,
            "device_health": incident.device_health,
            "incident_timestamp": incident.created_at.isoformat() if incident.created_at else get_utc_now().isoformat(),
            "simulate_tool_timeout": simulate_timeout,
            "audit_trail": []
        }

        # Run LangGraph Workflow
        config = {"configurable": {"thread_id": f"thread-{incident.id}"}}
        graph_output = await investigation_graph.ainvoke(initial_state, config)

        now_utc = get_utc_now()

        # 1. Save Investigation Findings
        diag = graph_output.get("diagnosis", {})
        investigation = InvestigationModel(
            incident_id=incident.id,
            status=graph_output.get("workflow_status", "COMPLETED"),
            likely_cause=diag.get("likely_cause", "Anomaly under investigation"),
            diagnosis_category=diag.get("diagnosis_category", "UNKNOWN"),
            observed_facts=diag.get("observed_facts", []),
            hypotheses=diag.get("hypotheses", []),
            uncertainty_notes=diag.get("uncertainty_notes", ""),
            retrieved_sop_citations=graph_output.get("sop_citations", []),
            recommended_action=graph_output.get("recommended_action", "HOVER_AND_DIAGNOSE"),
            recommended_action_params=graph_output.get("recommended_action_params", {}),
            preconditions=graph_output.get("preconditions", []),
            created_at=now_utc
        )
        db.add(investigation)
        incident.investigations.append(investigation)

        # 2. Save Policy Decision
        pol = graph_output.get("policy_decision", {})
        policy_decision = PolicyDecisionModel(
            incident_id=incident.id,
            investigation_id=investigation.id,
            action_type=graph_output.get("recommended_action", "HOVER_AND_DIAGNOSE"),
            outcome=pol.get("outcome", "BLOCK"),
            reasons=pol.get("reasons", []),
            failed_checks=pol.get("failed_checks", []),
            policy_ids_evaluated=pol.get("policy_ids_evaluated", []),
            evaluated_at=now_utc
        )
        db.add(policy_decision)
        incident.policy_decisions.append(policy_decision)

        # 3. Handle Branching Status & Side Effects
        outcome = pol.get("outcome")
        if outcome == "REQUIRES_APPROVAL":
            incident.status = "AWAITING_APPROVAL"
            approval_req = ApprovalRequestModel(
                incident_id=incident.id,
                action_type=graph_output.get("recommended_action", "DISPATCH_INSPECTION_DRONE"),
                action_params=graph_output.get("recommended_action_params", {}),
                status="PENDING",
                requested_at=now_utc
            )
            db.add(approval_req)
            incident.approval_requests.append(approval_req)
            
            audit_req = AuditEventModel(
                incident_id=incident.id,
                actor="system:policy_engine",
                event_type="APPROVAL_REQUESTED",
                payload={
                    "action_type": approval_req.action_type,
                    "reasons": pol.get("reasons", [])
                },
                timestamp=now_utc
            )
            db.add(audit_req)
            incident.audit_events.append(audit_req)

        elif outcome == "ALLOW":
            sim_result = graph_output.get("simulated_action_result", {})
            if sim_result:
                incident.status = "RESOLVED"
                sim_action = SimulatedActionModel(
                    incident_id=incident.id,
                    action_type=graph_output.get("recommended_action", "HOVER_AND_DIAGNOSE"),
                    action_params=graph_output.get("recommended_action_params", {}),
                    idempotency_key=f"action-{incident.id}-{graph_output.get('recommended_action')}",
                    status="EXECUTED",
                    executed_at=now_utc,
                    mock_result=sim_result
                )
                db.add(sim_action)
                incident.simulated_actions.append(sim_action)
            elif graph_output.get("workflow_status") == "ERROR":
                incident.status = "ERROR"
            else:
                incident.status = "RESOLVED"

        elif outcome in ("BLOCK", "INSUFFICIENT_EVIDENCE"):
            incident.status = "BLOCKED"

        # 4. Save Audit Events from Graph
        for audit in graph_output.get("audit_trail", []):
            try:
                dt = datetime.fromisoformat(audit.get("timestamp", "").replace("Z", "+00:00"))
            except Exception:
                dt = now_utc
            a_ev = AuditEventModel(
                incident_id=incident.id,
                actor=audit.get("actor", "system:workflow"),
                event_type=audit.get("event_type", "WORKFLOW_STEP"),
                payload=audit.get("payload", {}),
                timestamp=dt
            )
            db.add(a_ev)
            incident.audit_events.append(a_ev)

        await db.commit()
        return incident

    @staticmethod
    async def resolve_approval(
        incident_id: str,
        decision: str,
        operator_role: str,
        operator_id: str,
        rejection_reason: Optional[str],
        db: AsyncSession
    ) -> IncidentModel:
        incident = await IncidentService.get_incident(incident_id, db)

        # 1. Authorization check
        if operator_role == settings.VIEWER_ROLE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Authorization failure: Role '{operator_role}' is not permitted to resolve flight actions."
            )

        # 2. Find pending approval request
        approval_req = None
        for req in incident.approval_requests:
            if req.status == "PENDING":
                approval_req = req
                break

        if not approval_req:
            # Fallback query if not in loaded list
            stmt = (
                select(ApprovalRequestModel)
                .where(
                    ApprovalRequestModel.incident_id == incident_id,
                    ApprovalRequestModel.status == "PENDING"
                )
                .order_by(desc(ApprovalRequestModel.requested_at))
            )
            result = await db.execute(stmt)
            approval_req = result.scalar_one_or_none()
        
        if not approval_req:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No pending approval request found for incident {incident_id}"
            )

        now_utc = get_utc_now()
        decision_upper = decision.upper()

        if decision_upper == "REJECT":
            approval_req.status = "REJECTED"
            approval_req.resolved_at = now_utc
            approval_req.resolved_by = operator_id
            approval_req.operator_role = operator_role
            approval_req.rejection_reason = rejection_reason or "Rejected by operator"
            incident.status = "BLOCKED"

            rej_audit = AuditEventModel(
                incident_id=incident.id,
                actor=f"operator:{operator_id}",
                event_type="APPROVAL_RESOLVED",
                payload={
                    "decision": "REJECT",
                    "operator_role": operator_role,
                    "rejection_reason": approval_req.rejection_reason
                },
                timestamp=now_utc
            )
            db.add(rej_audit)
            incident.audit_events.append(rej_audit)
            await db.commit()
            return incident

        elif decision_upper == "APPROVE":
            # 3. Deterministic Safety Revalidation before execution
            revalidation = evaluate_safety_policy(
                proposed_action=approval_req.action_type,
                action_params=approval_req.action_params,
                telemetry=incident.telemetry_snapshot,
                incident_timestamp=incident.created_at,
                citations_count=1,
                conflicting_sop_detected=False,
                is_pre_execution_check=True,
                operator_role=operator_role
            )

            if revalidation.outcome == "BLOCK":
                approval_req.status = "REJECTED"
                approval_req.resolved_at = now_utc
                approval_req.resolved_by = operator_id
                approval_req.operator_role = operator_role
                approval_req.rejection_reason = f"Safety revalidation failed: {'; '.join(revalidation.reasons)}"
                incident.status = "BLOCKED"
                await db.commit()
                return incident

            # 4. Execute mock simulated action
            action_idempotency_key = f"action-{incident.id}-{approval_req.action_type}"
            exec_result = await mock_action_api.execute_simulated_action(
                drone_id=incident.drone_id,
                site_id=incident.site_id,
                action_type=approval_req.action_type,
                action_params=approval_req.action_params,
                idempotency_key=action_idempotency_key
            )

            # 5. Persist executed simulated action
            sim_action = SimulatedActionModel(
                incident_id=incident.id,
                action_type=approval_req.action_type,
                action_params=approval_req.action_params,
                idempotency_key=action_idempotency_key,
                status="EXECUTED",
                executed_at=now_utc,
                mock_result=exec_result
            )
            db.add(sim_action)
            incident.simulated_actions.append(sim_action)

            # Update approval & incident status
            approval_req.status = "APPROVED"
            approval_req.resolved_at = now_utc
            approval_req.resolved_by = operator_id
            approval_req.operator_role = operator_role
            incident.status = "RESOLVED"

            app_audit = AuditEventModel(
                incident_id=incident.id,
                actor=f"operator:{operator_id}",
                event_type="APPROVAL_RESOLVED",
                payload={
                    "decision": "APPROVE",
                    "operator_role": operator_role,
                    "simulated_execution": exec_result
                },
                timestamp=now_utc
            )
            db.add(app_audit)
            incident.audit_events.append(app_audit)
            await db.commit()
            return incident
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid decision '{decision}'. Must be 'APPROVE' or 'REJECT'."
            )

    @staticmethod
    async def list_incidents(
        db: AsyncSession,
        status_filter: Optional[str] = None,
        severity_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[IncidentModel]:
        stmt = (
            select(IncidentModel)
            .options(
                selectinload(IncidentModel.investigations),
                selectinload(IncidentModel.policy_decisions),
                selectinload(IncidentModel.approval_requests),
                selectinload(IncidentModel.simulated_actions),
                selectinload(IncidentModel.audit_events)
            )
            .order_by(desc(IncidentModel.created_at))
            .limit(limit)
        )
        if status_filter:
            stmt = stmt.where(IncidentModel.status == status_filter.upper())
        if severity_filter:
            stmt = stmt.where(IncidentModel.severity == severity_filter.upper())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> Dict[str, Any]:
        stmt = select(IncidentModel.status, func.count(IncidentModel.id)).group_by(IncidentModel.status)
        result = await db.execute(stmt)
        counts = dict(result.all())

        total = sum(counts.values())
        open_c = counts.get("OPEN", 0)
        investigating = counts.get("INVESTIGATING", 0)
        awaiting = counts.get("AWAITING_APPROVAL", 0)
        resolved = counts.get("RESOLVED", 0)
        blocked = counts.get("BLOCKED", 0)

        # Simulated fleet health roster
        fleet_health = [
            {
                "drone_id": "DRONE-01",
                "site_id": "SITE-ALPHA-01",
                "status": "PATROL_ACTIVE",
                "battery_pct": 82.5,
                "last_seen": get_utc_now()
            },
            {
                "drone_id": "DRONE-02",
                "site_id": "SITE-ALPHA-01",
                "status": "CHARGING_DOCK",
                "battery_pct": 98.0,
                "last_seen": get_utc_now()
            },
            {
                "drone_id": "DRONE-04",
                "site_id": "SITE-ALPHA-01",
                "status": "MAINTENANCE_HOLD",
                "battery_pct": 45.0,
                "last_seen": get_utc_now()
            },
            {
                "drone_id": "DRONE-09",
                "site_id": "SITE-PERIMETER-NORTH",
                "status": "STANDBY",
                "battery_pct": 91.0,
                "last_seen": get_utc_now()
            }
        ]

        return {
            "total_incidents": total,
            "open_incidents": open_c,
            "investigating_incidents": investigating,
            "awaiting_approval_incidents": awaiting,
            "resolved_incidents": resolved,
            "blocked_incidents": blocked,
            "fleet_health": fleet_health
        }
