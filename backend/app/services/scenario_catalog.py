from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.schemas.incident import IncidentCreate


def get_seeded_scenarios() -> List[Dict[str, Any]]:
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()
    stale_iso = (now_utc - timedelta(seconds=300)).isoformat()

    return [
        {
            "id": "low_battery",
            "name": "1. Low Battery Threshold Violation",
            "description": "Drone battery at 18% triggers critical alarm. Proposes dispatch of backup drone; deterministic safety policy strictly blocks dispatch due to reserve violation (<30%).",
            "event_type": "BATTERY_CRITICAL",
            "drone_id": "DRONE-03",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "BLOCKED",
            "expected_policy_decision": "BLOCK",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-03",
                "event_type": "BATTERY_CRITICAL",
                "severity": "HIGH",
                "idempotency_key": "scenario-low-battery-001",
                "telemetry_snapshot": {
                    "battery_pct": 18.0,
                    "altitude_m": 35.0,
                    "speed_mps": 4.1,
                    "gps_lat": 37.7745,
                    "gps_lon": -122.4180,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "ROUTINE_SOLAR_PATROL"},
                "device_health": {"notes": "battery cell 3 voltage sag, dispatch required"}
            }
        },
        {
            "id": "stale_telemetry",
            "name": "2. Stale Telemetry & Communication Lag",
            "description": "Telemetry feed timestamp is 300 seconds old (> 60s threshold). System flags stale evidence, defers flight movement, and restricts action to telemetry refresh request.",
            "event_type": "TELEMETRY_DESYNC",
            "drone_id": "DRONE-05",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "RESOLVED",
            "expected_policy_decision": "ALLOW",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-05",
                "event_type": "TELEMETRY_DESYNC",
                "severity": "MEDIUM",
                "idempotency_key": "scenario-stale-telemetry-002",
                "telemetry_snapshot": {
                    "battery_pct": 65.0,
                    "altitude_m": 50.0,
                    "speed_mps": 0.0,
                    "gps_lat": 37.7750,
                    "gps_lon": -122.4150,
                    "timestamp": stale_iso,
                    "heartbeat_ok": False
                },
                "mission_history": {"mission_name": "PERIMETER_MONITORING"},
                "device_health": {"notes": "rf packet loss, cell link intermittent"}
            }
        },
        {
            "id": "duplicate_webhook",
            "name": "3. Duplicate Webhook Intake & Action Idempotency",
            "description": "Submits identical intake webhook with idempotency key. Backend returns existing incident record and guarantees zero duplicate simulated actions.",
            "event_type": "SENSOR_FAILURE",
            "drone_id": "DRONE-01",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "RESOLVED",
            "expected_policy_decision": "ALLOW",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-01",
                "event_type": "SENSOR_FAILURE",
                "severity": "LOW",
                "idempotency_key": "scenario-duplicate-webhook-003",
                "telemetry_snapshot": {
                    "battery_pct": 85.0,
                    "altitude_m": 25.0,
                    "speed_mps": 3.0,
                    "gps_lat": 37.7752,
                    "gps_lon": -122.4160,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "ROOF_FACILITY_INSPECTION"},
                "device_health": {"camera_status": "PAYLOAD_BUS_ERROR"}
            }
        },
        {
            "id": "no_relevant_sop",
            "name": "4. No Relevant SOP Found in Knowledge Base",
            "description": "Incident triggered with unknown procedural anomaly. ChromaDB returns zero relevant SOP citations. System flags INSUFFICIENT_EVIDENCE rather than hallucinating procedures.",
            "event_type": "UNKNOWN_SIGNAL_OR_SOP",
            "drone_id": "DRONE-07",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "BLOCKED",
            "expected_policy_decision": "INSUFFICIENT_EVIDENCE",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-07",
                "event_type": "UNKNOWN_SIGNAL_OR_SOP",
                "severity": "HIGH",
                "idempotency_key": "scenario-no-sop-004",
                "telemetry_snapshot": {
                    "battery_pct": 55.0,
                    "altitude_m": 40.0,
                    "speed_mps": 2.0,
                    "gps_lat": 37.7740,
                    "gps_lon": -122.4170,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "ANOMALY_PATROL"},
                "device_health": {"notes": "unrecognized sensor code 0x99FF unknown telemetry frequency"}
            }
        },
        {
            "id": "conflicting_sops",
            "name": "5. Conflicting Standard Operating Procedures",
            "description": "Perimeter alarm in high-wind conditions retrieves conflicting SOP-005 directives (Ascend 100m vs Descend 15m). Workflow pauses and requires human flight supervisor approval.",
            "event_type": "HIGH_WIND_PERIMETER_BREACH",
            "drone_id": "DRONE-02",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "AWAITING_APPROVAL",
            "expected_policy_decision": "REQUIRES_APPROVAL",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-02",
                "event_type": "HIGH_WIND_PERIMETER_BREACH",
                "severity": "CRITICAL",
                "idempotency_key": "scenario-conflicting-sops-005",
                "telemetry_snapshot": {
                    "battery_pct": 78.0,
                    "altitude_m": 30.0,
                    "speed_mps": 6.5,
                    "gps_lat": 37.7760,
                    "gps_lon": -122.4130,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "PERIMETER_SURVEILLANCE"},
                "device_health": {"notes": "wind sensor gust 18 m/s, fence vibration sensor active"}
            }
        },
        {
            "id": "unauthorized_operator",
            "name": "6. Unauthorized Operator Approval Attempt",
            "description": "An operator with 'viewer' role attempts to authorize a pending flight response. Backend authorization gate rejects the command with HTTP 403 Forbidden.",
            "event_type": "HIGH_WIND_PERIMETER_BREACH",
            "drone_id": "DRONE-02",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "FORBIDDEN",
            "expected_policy_decision": "REQUIRES_APPROVAL",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-02",
                "event_type": "HIGH_WIND_PERIMETER_BREACH",
                "severity": "HIGH",
                "idempotency_key": "scenario-unauthorized-auth-006",
                "telemetry_snapshot": {
                    "battery_pct": 78.0,
                    "altitude_m": 30.0,
                    "speed_mps": 6.5,
                    "gps_lat": 37.7760,
                    "gps_lon": -122.4130,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "PERIMETER_SURVEILLANCE"},
                "device_health": {"notes": "wind sensor gust 16 m/s"}
            }
        },
        {
            "id": "tool_timeout",
            "name": "7. Simulated Telemetry Tool Timeout & Fault Recovery",
            "description": "Simulates a transient telemetry API timeout during simulated execution. System records failure in audit events, preserves workflow state, and marks status without crash.",
            "event_type": "SENSOR_FAILURE",
            "drone_id": "DRONE-06",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "ERROR",
            "expected_policy_decision": "ALLOW",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-06",
                "event_type": "SENSOR_FAILURE",
                "severity": "MEDIUM",
                "idempotency_key": "scenario-tool-timeout-007",
                "telemetry_snapshot": {
                    "battery_pct": 60.0,
                    "altitude_m": 40.0,
                    "speed_mps": 2.0,
                    "gps_lat": 37.7750,
                    "gps_lon": -122.4160,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "SURVEY_MISSION"},
                "device_health": {"camera_status": "PAYLOAD_BUS_ERROR"}
            }
        },
        {
            "id": "geofence_violation",
            "name": "8. Geofence Boundary Containment Breach",
            "description": "Drone coordinates target a waypoint outside the certified Site Alpha bounding box. Deterministic policy unconditionally BLOCKS the prohibited flight action.",
            "event_type": "GEOFENCE_BREACH",
            "drone_id": "DRONE-08",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "BLOCKED",
            "expected_policy_decision": "BLOCK",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-08",
                "event_type": "GEOFENCE_BREACH",
                "severity": "CRITICAL",
                "idempotency_key": "scenario-geofence-breach-008",
                "telemetry_snapshot": {
                    "battery_pct": 68.0,
                    "altitude_m": 55.0,
                    "speed_mps": 8.0,
                    "gps_lat": 37.7950,  # Outside Site Alpha (max 37.7800)
                    "gps_lon": -122.4350, # Outside Site Alpha (min -122.4200)
                    "target_lat": 37.7950,
                    "target_lon": -122.4350,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "PERIMETER_EAST"},
                "device_health": {"notes": "boundary warning beacon active"}
            }
        },
        {
            "id": "normal_patrol_failure",
            "name": "9. Normal Patrol Failure (Happy Path Investigation)",
            "description": "Camera optical sensor glitch on Drone-04 during perimeter patrol. Telemetry is fresh, battery healthy (72%), SOP-004 retrieved. Policy allows safe diagnostic hover, and incident resolves.",
            "event_type": "SENSOR_FAILURE",
            "drone_id": "DRONE-04",
            "site_id": "SITE-ALPHA-01",
            "expected_outcome": "RESOLVED",
            "expected_policy_decision": "ALLOW",
            "payload": {
                "site_id": "SITE-ALPHA-01",
                "drone_id": "DRONE-04",
                "event_type": "SENSOR_FAILURE",
                "severity": "MEDIUM",
                "idempotency_key": "scenario-patrol-failure-009",
                "telemetry_snapshot": {
                    "battery_pct": 72.0,
                    "altitude_m": 45.0,
                    "speed_mps": 4.5,
                    "gps_lat": 37.7750,
                    "gps_lon": -122.4160,
                    "timestamp": now_iso,
                    "heartbeat_ok": True
                },
                "mission_history": {"mission_name": "PERIMETER_NORTH_PATROL"},
                "device_health": {"camera_status": "PAYLOAD_BUS_ERROR", "vibration_level": "NORMAL"}
            }
        }
    ]


def get_scenario_by_id(scenario_id: str) -> Optional[Dict[str, Any]]:
    for s in get_seeded_scenarios():
        if s["id"] == scenario_id:
            return s
    return None
