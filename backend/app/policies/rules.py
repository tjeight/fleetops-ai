from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from app.core.config import settings

# Explicit allowlist of harmless simulated actions
ALLOWED_SIMULATED_ACTIONS = {
    "RTH_EMERGENCY",
    "HOVER_AND_DIAGNOSE",
    "TELEMETRY_REFRESH_REQUEST",
    "LAND_IMMEDIATE_SAFE",
    "DISPATCH_INSPECTION_DRONE",
}

# Actions requiring human flight supervisor approval
APPROVAL_REQUIRED_ACTIONS = {
    "DISPATCH_INSPECTION_DRONE",
}


class PolicyEvaluationResult(BaseModel):
    outcome: str  # "ALLOW", "BLOCK", "REQUIRES_APPROVAL", "INSUFFICIENT_EVIDENCE"
    reasons: List[str]
    failed_checks: List[str]
    policy_ids_evaluated: List[str]


def evaluate_safety_policy(
    proposed_action: str,
    action_params: Dict[str, Any],
    telemetry: Dict[str, Any],
    incident_timestamp: datetime,
    citations_count: int,
    conflicting_sop_detected: bool = False,
    is_pre_execution_check: bool = False,
    operator_role: Optional[str] = None
) -> PolicyEvaluationResult:
    """
    Deterministic Python safety gate.
    Validates every proposed action completely independently of the LLM.
    """
    policy_ids: List[str] = []
    failed_checks: List[str] = []
    reasons: List[str] = []

    # 1. Allowlist Policy (POL-ALLOWLIST-01)
    policy_ids.append("POL-ALLOWLIST-01")
    if proposed_action not in ALLOWED_SIMULATED_ACTIONS:
        failed_checks.append("POL-ALLOWLIST-01")
        reasons.append(f"Action '{proposed_action}' is not in the authorized simulated action allowlist.")
        return PolicyEvaluationResult(
            outcome="BLOCK",
            reasons=reasons,
            failed_checks=failed_checks,
            policy_ids_evaluated=policy_ids
        )

    # 2. Procedural Evidence Policy (POL-RAG-01)
    policy_ids.append("POL-RAG-01")
    if citations_count == 0:
        failed_checks.append("POL-RAG-01")
        reasons.append("Insufficient procedural evidence: No relevant SOP found in knowledge base for this incident.")
        return PolicyEvaluationResult(
            outcome="INSUFFICIENT_EVIDENCE",
            reasons=reasons,
            failed_checks=failed_checks,
            policy_ids_evaluated=policy_ids
        )

    # 3. Telemetry Freshness & Completeness (POL-FRESHNESS-01)
    policy_ids.append("POL-FRESHNESS-01")
    if not telemetry or "timestamp" not in telemetry:
        failed_checks.append("POL-FRESHNESS-01")
        reasons.append("Telemetry snapshot is missing or contains no timestamp.")
        return PolicyEvaluationResult(
            outcome="INSUFFICIENT_EVIDENCE",
            reasons=reasons,
            failed_checks=failed_checks,
            policy_ids_evaluated=policy_ids
        )

    # Calculate telemetry age
    raw_telemetry_time = telemetry.get("timestamp")
    if isinstance(raw_telemetry_time, str):
        try:
            telem_dt = datetime.fromisoformat(raw_telemetry_time.replace("Z", "+00:00"))
        except Exception:
            telem_dt = incident_timestamp
    elif isinstance(raw_telemetry_time, datetime):
        telem_dt = raw_telemetry_time
    else:
        telem_dt = incident_timestamp

    if incident_timestamp.tzinfo is None:
        incident_timestamp = incident_timestamp.replace(tzinfo=timezone.utc)
    if telem_dt.tzinfo is None:
        telem_dt = telem_dt.replace(tzinfo=timezone.utc)

    telemetry_age_seconds = abs((incident_timestamp - telem_dt).total_seconds())
    
    if telemetry_age_seconds > settings.TELEMETRY_MAX_AGE_SECONDS:
        # Telemetry is stale
        if proposed_action != "TELEMETRY_REFRESH_REQUEST":
            failed_checks.append("POL-FRESHNESS-01")
            reasons.append(
                f"Telemetry age ({telemetry_age_seconds:.1f}s) exceeds maximum allowable threshold ({settings.TELEMETRY_MAX_AGE_SECONDS}s). Flight maneuvers prohibited."
            )
            return PolicyEvaluationResult(
                outcome="BLOCK",
                reasons=reasons,
                failed_checks=failed_checks,
                policy_ids_evaluated=policy_ids
            )

    # 4. Geofence Boundary Check (POL-GEOFENCE-01)
    policy_ids.append("POL-GEOFENCE-01")
    # Check current telemetry position
    cur_lat = telemetry.get("gps_lat")
    cur_lon = telemetry.get("gps_lon")
    
    # Check target waypoint if specified in action parameters
    target_lat = action_params.get("target_lat", cur_lat)
    target_lon = action_params.get("target_lon", cur_lon)

    if target_lat is not None and target_lon is not None:
        is_outside_geofence = (
            target_lat < settings.GEOFENCE_MIN_LAT or
            target_lat > settings.GEOFENCE_MAX_LAT or
            target_lon < settings.GEOFENCE_MIN_LON or
            target_lon > settings.GEOFENCE_MAX_LON
        )
        if is_outside_geofence:
            failed_checks.append("POL-GEOFENCE-01")
            reasons.append(
                f"Coordinates ({target_lat}, {target_lon}) violate operational geofence bounds "
                f"[{settings.GEOFENCE_MIN_LAT} to {settings.GEOFENCE_MAX_LAT}, {settings.GEOFENCE_MIN_LON} to {settings.GEOFENCE_MAX_LON}]."
            )
            return PolicyEvaluationResult(
                outcome="BLOCK",
                reasons=reasons,
                failed_checks=failed_checks,
                policy_ids_evaluated=policy_ids
            )

    # 5. Battery Reserve Policy (POL-BATTERY-01)
    policy_ids.append("POL-BATTERY-01")
    battery_pct = telemetry.get("battery_pct", 0.0)
    
    # Prohibit dispatch if battery < 30%
    if proposed_action in ("DISPATCH_INSPECTION_DRONE",) and battery_pct < settings.BATTERY_DISPATCH_MIN_PCT:
        failed_checks.append("POL-BATTERY-01")
        reasons.append(
            f"Battery capacity ({battery_pct:.1f}%) is below minimum required reserve ({settings.BATTERY_DISPATCH_MIN_PCT}%) for dispatch."
        )
        return PolicyEvaluationResult(
            outcome="BLOCK",
            reasons=reasons,
            failed_checks=failed_checks,
            policy_ids_evaluated=policy_ids
        )

    # 6. Procedural Conflict Policy (POL-CONFLICT-01)
    policy_ids.append("POL-CONFLICT-01")
    if conflicting_sop_detected and not is_pre_execution_check:
        reasons.append("Conflicting operating procedures detected. Mandatory operator review required.")
        return PolicyEvaluationResult(
            outcome="REQUIRES_APPROVAL",
            reasons=reasons,
            failed_checks=failed_checks,
            policy_ids_evaluated=policy_ids
        )

    # 7. Operator Authorization Check (POL-AUTH-01) - evaluated during approval or execution
    policy_ids.append("POL-AUTH-01")
    if operator_role:
        if operator_role == settings.VIEWER_ROLE:
            failed_checks.append("POL-AUTH-01")
            reasons.append(f"Operator role '{operator_role}' is not authorized to execute or approve operational commands.")
            return PolicyEvaluationResult(
                outcome="BLOCK",
                reasons=reasons,
                failed_checks=failed_checks,
                policy_ids_evaluated=policy_ids
            )

    # 8. Human Approval Policy (POL-APPROVAL-01)
    policy_ids.append("POL-APPROVAL-01")
    if proposed_action in APPROVAL_REQUIRED_ACTIONS and not is_pre_execution_check:
        reasons.append(f"Action '{proposed_action}' is designated as high-consequence and requires human approval before execution.")
        return PolicyEvaluationResult(
            outcome="REQUIRES_APPROVAL",
            reasons=reasons,
            failed_checks=failed_checks,
            policy_ids_evaluated=policy_ids
        )

    # All safety checks passed
    reasons.append(f"All deterministic safety constraints validated successfully for action '{proposed_action}'.")
    return PolicyEvaluationResult(
        outcome="ALLOW",
        reasons=reasons,
        failed_checks=[],
        policy_ids_evaluated=policy_ids
    )
