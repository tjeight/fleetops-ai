import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.core.config import settings
from app.policies.rules import evaluate_safety_policy
from app.retrieval.chroma_store import retriever
from app.tools.mock_action_api import (
    MockActionExecutionError,
    MockActionTimeoutError,
    mock_action_api,
)


class InvestigationState(TypedDict):
    incident_id: str
    site_id: str
    drone_id: str
    event_type: str
    severity: str
    telemetry_snapshot: Dict[str, Any]
    mission_history: Dict[str, Any]
    device_health: Dict[str, Any]
    incident_timestamp: str
    freshness_flags: Dict[str, Any]
    sop_citations: List[Dict[str, Any]]
    conflicting_sop_detected: bool
    diagnosis: Dict[str, Any]
    recommended_action: str
    recommended_action_params: Dict[str, Any]
    preconditions: List[str]
    policy_decision: Dict[str, Any]
    simulated_action_result: Dict[str, Any]
    workflow_status: str
    audit_trail: List[Dict[str, Any]]
    simulate_tool_timeout: bool
    error_message: Optional[str]


# ---------------------------------------------------------
# Node 1: Evidence Validation & Freshness Check
# ---------------------------------------------------------
def node_validate_and_check_freshness(state: InvestigationState) -> Dict[str, Any]:
    incident_id = state["incident_id"]
    telemetry = state.get("telemetry_snapshot", {})
    now_utc = datetime.now(timezone.utc)

    # Parse incident intake time
    raw_time = state.get("incident_timestamp")
    try:
        incident_dt = (
            datetime.fromisoformat(raw_time.replace("Z", "+00:00")) if raw_time else now_utc
        )
    except Exception:
        incident_dt = now_utc

    # Freshness check
    is_missing = not bool(telemetry) or "timestamp" not in telemetry
    is_stale = False
    telemetry_age_seconds = 0.0

    if not is_missing:
        raw_telem_ts = telemetry.get("timestamp")
        try:
            if isinstance(raw_telem_ts, str):
                telem_dt = datetime.fromisoformat(raw_telem_ts.replace("Z", "+00:00"))
            else:
                telem_dt = raw_telem_ts
            if telem_dt.tzinfo is None:
                telem_dt = telem_dt.replace(tzinfo=timezone.utc)
            telemetry_age_seconds = max(0.0, (incident_dt - telem_dt).total_seconds())
            if telemetry_age_seconds > settings.TELEMETRY_MAX_AGE_SECONDS:
                is_stale = True
        except Exception:
            is_stale = True

    freshness_flags = {
        "is_missing": is_missing,
        "is_stale": is_stale,
        "telemetry_age_seconds": round(telemetry_age_seconds, 1),
        "heartbeat_ok": telemetry.get("heartbeat_ok", not is_stale),
        "evaluated_at": now_utc.isoformat(),
    }

    audit_entry = {
        "actor": "system:freshness_checker",
        "event_type": "TELEMETRY_CHECKED",
        "payload": freshness_flags,
        "timestamp": now_utc.isoformat(),
    }

    return {
        "freshness_flags": freshness_flags,
        "workflow_status": "INVESTIGATING",
        "audit_trail": state.get("audit_trail", []) + [audit_entry],
    }


# ---------------------------------------------------------
# Node 2: SOP Retrieval from ChromaDB
# ---------------------------------------------------------
def node_retrieve_sops(state: InvestigationState) -> Dict[str, Any]:
    event_type = state.get("event_type", "")
    device_health = state.get("device_health", {})
    health_details = " ".join(str(v) for k, v in device_health.items() if v)

    # Formulate domain-specific retrieval query
    if event_type in ("BATTERY_CRITICAL", "LOW_BATTERY"):
        query = "Low battery emergency return RTH landing reserve policy SOP-001"
    elif event_type in ("TELEMETRY_DESYNC", "STALE_TELEMETRY"):
        query = "Telemetry staleness communication loss desync heartbeat SOP-002"
    elif event_type in ("GEOFENCE_BREACH", "AIRSPACE_VIOLATION"):
        query = "Airspace geofence boundary containment exclusion zone SOP-003"
    elif event_type in ("HIGH_WIND_PERIMETER_BREACH", "CONFLICTING_SOPS"):
        query = "High wind perimeter breach conflicting directive protocol SOP-005"
    elif event_type in ("SENSOR_FAILURE", "CAMERA_FAILURE", "PATROL_FAILURE"):
        query = f"Camera optical sensor failure patrol malfunction gimbal {health_details} SOP-004"
    else:
        query = f"{event_type} {health_details} drone operational safety procedure"

    min_similarity = 0.30 if event_type != "UNKNOWN_SIGNAL_OR_SOP" else 0.50
    citations = retriever.retrieve(query=query, top_k=3, min_similarity=min_similarity)
    now_utc = datetime.now(timezone.utc).isoformat()

    # Detect procedural conflict (SOP-005)
    conflicting_sop_detected = event_type in (
        "HIGH_WIND_PERIMETER_BREACH",
        "CONFLICTING_SOPS",
    ) or any(
        "SOP-005" in c.get("sop_id", "") for c in citations if c.get("relevance_score", 0) >= 0.40
    )

    audit_entry = {
        "actor": "system:sop_retriever",
        "event_type": "SOP_RETRIEVED",
        "payload": {
            "query": query,
            "citations_found": len(citations),
            "sop_ids": [c.get("sop_id") for c in citations],
            "conflicting_sop_detected": conflicting_sop_detected,
        },
        "timestamp": now_utc,
    }

    return {
        "sop_citations": citations,
        "conflicting_sop_detected": conflicting_sop_detected,
        "audit_trail": state.get("audit_trail", []) + [audit_entry],
    }


# ---------------------------------------------------------
# Node 3: Synthesize Structured Diagnosis & Recommendation
# ---------------------------------------------------------
def node_synthesize_diagnosis(state: InvestigationState) -> Dict[str, Any]:
    event_type = state.get("event_type", "")
    telemetry = state.get("telemetry_snapshot", {})
    health = state.get("device_health", {})
    mission = state.get("mission_history", {})
    freshness = state.get("freshness_flags", {})
    citations = state.get("sop_citations", [])
    conflicting = state.get("conflicting_sop_detected", False)

    battery_pct = telemetry.get("battery_pct", 100.0)
    is_stale = freshness.get("is_stale", False)
    is_missing = freshness.get("is_missing", False)

    # Grounded diagnosis synthesis
    observed_facts: List[str] = []
    hypotheses: List[str] = []
    uncertainty_notes: List[str] = []

    if is_missing:
        observed_facts.append("No active telemetry stream received from drone flight controller.")
        uncertainty_notes.append(
            "Telemetry is absent; unable to establish drone coordinates or flight state."
        )
        likely_cause = "Missing telemetry prevents conclusive diagnosis."
        diagnosis_category = "TELEMETRY_DESYNC"
        recommended_action = "TELEMETRY_REFRESH_REQUEST"
        rec_params = {"priority": "URGENT"}
        preconditions = ["Cellular radio link active", "Ground station gateway alive"]

    elif is_stale:
        observed_facts.append(
            f"Telemetry packet timestamp is {freshness.get('telemetry_age_seconds')}s old (threshold is {settings.TELEMETRY_MAX_AGE_SECONDS}s)."
        )
        observed_facts.append(f"Last recorded battery level: {battery_pct}%.")
        hypotheses.append("RF link degradation or cellular handover lag caused packet buffering.")
        uncertainty_notes.append(
            "Flight state may have changed since last telemetry update. Do not execute blind movements."
        )
        likely_cause = "Telemetry desynchronization / stale data received during mission."
        diagnosis_category = "TELEMETRY_DESYNC"
        recommended_action = "TELEMETRY_REFRESH_REQUEST"
        rec_params = {"poll_interval_ms": 500}
        preconditions = ["Heartbeat ACK received before issuing subsequent flight commands"]

    elif not citations:
        observed_facts.append(f"Incident triggered with event type: '{event_type}'.")
        observed_facts.append(f"Drone battery at {battery_pct}%, GPS position recorded.")
        hypotheses.append(
            "Incident event type not covered in active standard operating procedures."
        )
        uncertainty_notes.append(
            "Insufficient procedural evidence: Zero matching SOP passages in knowledge base."
        )
        likely_cause = "Unrecognized operational anomaly without documented procedural guidance."
        diagnosis_category = "UNKNOWN_PROCEDURE"
        recommended_action = "HOVER_AND_DIAGNOSE"
        rec_params = {"duration_seconds": 30}
        preconditions = ["Operator manual review recommended"]

    elif conflicting:
        observed_facts.append(
            "Perimeter fence alarm triggered during high-wind condition (> 15 m/s)."
        )
        observed_facts.append(f"Drone battery healthy at {battery_pct}%.")
        hypotheses.append(
            "Contradictory operational protocols: Directive A requires high altitude visual sweep, Directive B mandates low altitude hover."
        )
        uncertainty_notes.append(
            "Conflicting operating procedures detected between tactical security and aerodynamic flight safety."
        )
        likely_cause = "Procedural directive conflict during extreme weather perimeter alarm."
        diagnosis_category = "EXTREME_WEATHER_CONFLICT"
        recommended_action = "DISPATCH_INSPECTION_DRONE"
        rec_params = {"target_perimeter": "NORTH_SECTOR", "dock_id": "DOCK-ALPHA"}
        preconditions = [
            "Flight supervisor manual authorization required to resolve directive conflict"
        ]

    elif event_type in ("BATTERY_CRITICAL", "LOW_BATTERY"):
        observed_facts.append(f"Drone battery capacity measured at {battery_pct}%.")
        observed_facts.append(
            f"Current altitude {telemetry.get('altitude_m', 0)}m, speed {telemetry.get('speed_mps', 0)}m/s."
        )
        hypotheses.append("Rapid cell discharge or mission duration exceeded energy budget.")
        uncertainty_notes.append("Battery discharge curve may steepen under headwind conditions.")
        likely_cause = f"Critical low battery state ({battery_pct}% remaining capacity)."
        diagnosis_category = "BATTERY_DEPLETION"

        # If low battery scenario specifically requests an unsafe dispatch (Scenario 1), propose dispatch to test safety gate
        if (
            state.get("severity") == "HIGH"
            and battery_pct < 25.0
            and "dispatch" in str(state.get("device_health", "")).lower()
        ):
            recommended_action = "DISPATCH_INSPECTION_DRONE"
            rec_params = {"target_lat": 37.7760, "target_lon": -122.4140}
            preconditions = ["Battery reserve check mandatory"]
        elif battery_pct <= 15.0:
            recommended_action = "LAND_IMMEDIATE_SAFE"
            rec_params = {"descent_rate_mps": 1.2}
            preconditions = ["Ground clearance sensor verified"]
        else:
            recommended_action = "RTH_EMERGENCY"
            rec_params = {"dock_coordinates": {"lat": 37.7750, "lon": -122.4150}}
            preconditions = ["Return path clear of obstacles"]

    elif event_type in ("GEOFENCE_BREACH", "AIRSPACE_VIOLATION"):
        lat = telemetry.get("gps_lat", 0.0)
        lon = telemetry.get("gps_lon", 0.0)
        observed_facts.append(
            f"Drone waypoint or current position ({lat}, {lon}) breaches certified bounding box."
        )
        hypotheses.append("Waypoint entry error or GPS multipath drift near site boundary.")
        uncertainty_notes.append("GPS signal HDOP acceptable; confirmed physical breach.")
        likely_cause = "Airspace boundary geofence breach detected."
        diagnosis_category = "GEOFENCE_RISK"
        recommended_action = "RTH_EMERGENCY"
        rec_params = {
            # In Scenario 8, test whether geofence gate blocks target waypoint outside boundary
            "target_lat": telemetry.get("target_lat", 37.7950),
            "target_lon": telemetry.get("target_lon", -122.4350),
        }
        preconditions = ["Immediate containment protocol"]

    else:
        # Default / Normal patrol failure (Scenario 9)
        vibration = health.get("vibration_level", "NORMAL")
        camera_error = health.get("camera_status", "PAYLOAD_BUS_ERROR")
        observed_facts.append(f"Optical sensor error reported: {camera_error}.")
        observed_facts.append(
            f"Motor vibration level: {vibration}. Battery capacity: {battery_pct}%."
        )
        hypotheses.append("Camera payload gimbal lock or optical bus desync.")
        uncertainty_notes.append("Airframe integrity and propulsion nominal; payload failure only.")
        likely_cause = "Optical camera sensor communication failure during perimeter patrol."
        diagnosis_category = "PAYLOAD_FAULT"
        recommended_action = "HOVER_AND_DIAGNOSE"
        rec_params = {"duration_seconds": 30}
        preconditions = ["Stable hover position hold", "Propulsion systems nominal"]

    diagnosis = {
        "likely_cause": likely_cause,
        "diagnosis_category": diagnosis_category,
        "observed_facts": observed_facts,
        "hypotheses": hypotheses,
        "uncertainty_notes": " | ".join(uncertainty_notes)
        if uncertainty_notes
        else "None detected.",
    }

    now_utc = datetime.now(timezone.utc).isoformat()
    audit_entry = {
        "actor": "system:langgraph_investigator",
        "event_type": "DIAGNOSIS_GENERATED",
        "payload": {
            "diagnosis_category": diagnosis_category,
            "recommended_action": recommended_action,
            "citations_used": [c.get("sop_id") for c in citations],
        },
        "timestamp": now_utc,
    }

    return {
        "diagnosis": diagnosis,
        "recommended_action": recommended_action,
        "recommended_action_params": rec_params,
        "preconditions": preconditions,
        "audit_trail": state.get("audit_trail", []) + [audit_entry],
    }


# ---------------------------------------------------------
# Node 4: Deterministic Python Safety Gate
# ---------------------------------------------------------
def node_evaluate_policy(state: InvestigationState) -> Dict[str, Any]:
    proposed_action = state.get("recommended_action", "HOVER_AND_DIAGNOSE")
    action_params = state.get("recommended_action_params", {})
    telemetry = state.get("telemetry_snapshot", {})
    citations = state.get("sop_citations", [])
    conflicting = state.get("conflicting_sop_detected", False)

    raw_time = state.get("incident_timestamp")
    now_utc = datetime.now(timezone.utc)
    try:
        incident_dt = (
            datetime.fromisoformat(raw_time.replace("Z", "+00:00")) if raw_time else now_utc
        )
    except Exception:
        incident_dt = now_utc

    policy_result = evaluate_safety_policy(
        proposed_action=proposed_action,
        action_params=action_params,
        telemetry=telemetry,
        incident_timestamp=incident_dt,
        citations_count=len(citations),
        conflicting_sop_detected=conflicting,
        is_pre_execution_check=False,
        operator_role=None,
    )

    policy_dict = policy_result.model_dump()
    outcome = policy_result.outcome

    # Map policy outcome to workflow status
    if outcome == "ALLOW":
        workflow_status = "INVESTIGATING"  # proceed to execute
    elif outcome == "REQUIRES_APPROVAL":
        workflow_status = "AWAITING_APPROVAL"
    elif outcome == "BLOCK":
        workflow_status = "BLOCKED"
    else:  # INSUFFICIENT_EVIDENCE
        workflow_status = "BLOCKED"

    audit_entry = {
        "actor": "system:deterministic_policy_gate",
        "event_type": "POLICY_EVALUATED",
        "payload": {
            "action_type": proposed_action,
            "outcome": outcome,
            "reasons": policy_result.reasons,
            "failed_checks": policy_result.failed_checks,
        },
        "timestamp": now_utc.isoformat(),
    }

    return {
        "policy_decision": policy_dict,
        "workflow_status": workflow_status,
        "audit_trail": state.get("audit_trail", []) + [audit_entry],
    }


# ---------------------------------------------------------
# Node 5: Simulated Action Executor (Mock Boundary)
# ---------------------------------------------------------
async def node_execute_mock_action(state: InvestigationState) -> Dict[str, Any]:
    action_type = state.get("recommended_action", "")
    action_params = state.get("recommended_action_params", {})
    drone_id = state.get("drone_id", "")
    site_id = state.get("site_id", "")
    incident_id = state.get("incident_id", "")
    simulate_timeout = state.get("simulate_tool_timeout", False)
    idempotency_key = f"action-{incident_id}-{action_type}"
    now_utc = datetime.now(timezone.utc).isoformat()

    try:
        execution_result = await mock_action_api.execute_simulated_action(
            drone_id=drone_id,
            site_id=site_id,
            action_type=action_type,
            action_params=action_params,
            idempotency_key=idempotency_key,
            simulate_timeout=simulate_timeout,
        )

        audit_entry = {
            "actor": "system:mock_action_executor",
            "event_type": "ACTION_EXECUTED",
            "payload": {"action_type": action_type, "execution_result": execution_result},
            "timestamp": now_utc,
        }

        return {
            "simulated_action_result": execution_result,
            "workflow_status": "RESOLVED",
            "audit_trail": state.get("audit_trail", []) + [audit_entry],
        }

    except MockActionTimeoutError as e:
        audit_entry = {
            "actor": "system:mock_action_executor",
            "event_type": "ACTION_FAILED_TIMEOUT",
            "payload": {"action_type": action_type, "error": str(e)},
            "timestamp": now_utc,
        }
        return {
            "error_message": f"Action execution timed out: {str(e)}",
            "workflow_status": "ERROR",
            "audit_trail": state.get("audit_trail", []) + [audit_entry],
        }
    except Exception as e:
        audit_entry = {
            "actor": "system:mock_action_executor",
            "event_type": "ACTION_FAILED",
            "payload": {"action_type": action_type, "error": str(e)},
            "timestamp": now_utc,
        }
        return {
            "error_message": str(e),
            "workflow_status": "ERROR",
            "audit_trail": state.get("audit_trail", []) + [audit_entry],
        }


# ---------------------------------------------------------
# Node 6: Finalize Investigation
# ---------------------------------------------------------
def node_finalize_investigation(state: InvestigationState) -> Dict[str, Any]:
    return {}


# ---------------------------------------------------------
# Routing Condition
# ---------------------------------------------------------
def route_after_policy(state: InvestigationState) -> str:
    policy = state.get("policy_decision", {})
    outcome = policy.get("outcome")
    if outcome == "ALLOW":
        return "execute_mock_action"
    return "finalize_investigation"


# ---------------------------------------------------------
# Graph Construction & Compilation
# ---------------------------------------------------------
def build_investigation_graph():
    builder = StateGraph(InvestigationState)

    # Add Nodes
    builder.add_node("validate_and_check_freshness", node_validate_and_check_freshness)
    builder.add_node("retrieve_sops", node_retrieve_sops)
    builder.add_node("synthesize_diagnosis", node_synthesize_diagnosis)
    builder.add_node("evaluate_policy", node_evaluate_policy)
    builder.add_node("execute_mock_action", node_execute_mock_action)
    builder.add_node("finalize_investigation", node_finalize_investigation)

    # Add Flow Edges
    builder.add_edge(START, "validate_and_check_freshness")
    builder.add_edge("validate_and_check_freshness", "retrieve_sops")
    builder.add_edge("retrieve_sops", "synthesize_diagnosis")
    builder.add_edge("synthesize_diagnosis", "evaluate_policy")

    # Conditional Branching
    builder.add_conditional_edges(
        "evaluate_policy",
        route_after_policy,
        {
            "execute_mock_action": "execute_mock_action",
            "finalize_investigation": "finalize_investigation",
        },
    )

    builder.add_edge("execute_mock_action", "finalize_investigation")
    builder.add_edge("finalize_investigation", END)

    # Persistent Memory Checkpointer for Approval Pause/Resume
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


investigation_graph = build_investigation_graph()
