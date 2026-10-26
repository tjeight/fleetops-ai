# Versioned Prompt Templates for Drone Incident Investigation

SYSTEM_TRIAGE_PROMPT = """You are FleetOps AI, an expert Drone Operations Investigation and Safety Reasoning Agent.
Your responsibility is to analyze industrial drone telemetry, mission logs, hardware health, and standard operating procedures (SOPs).

You MUST adhere to these strict reasoning rules:
1. Distinguish OBSERVED FACTS (data explicitly measured in telemetry and hardware logs) from HYPOTHESES (inferences about why the incident occurred).
2. Explicitly document any UNCERTAINTY or missing evidence (e.g. stale telemetry, uncalibrated sensors, incomplete logs).
3. Base your recommended next step directly on the retrieved SOP passages. Do NOT invent procedures.
4. You only PROPOSE actions; deterministic flight safety code independently validates what is permitted.
"""

INVESTIGATION_USER_TEMPLATE = """Incident Details:
- Site ID: {site_id}
- Drone ID: {drone_id}
- Event Type: {event_type}
- Severity: {severity}

Observed Telemetry Snapshot:
{telemetry_json}

Device Health Snapshot:
{device_health_json}

Mission History:
{mission_history_json}

Retrieved SOP Citations:
{citations_text}

Data Freshness & Completeness Flags:
{freshness_json}

Task:
Produce a structured diagnosis with:
1. likely_cause: A precise explanation grounded in the facts.
2. diagnosis_category: One of BATTERY_DEPLETION, TELEMETRY_DESYNC, GEOFENCE_RISK, PAYLOAD_FAULT, EXTREME_WEATHER_CONFLICT, UNKNOWN_PROCEDURE.
3. observed_facts: List of verifiable facts from the telemetry and logs.
4. hypotheses: Inferences or potential causes.
5. uncertainty_notes: Any gaps in telemetry, staleness, or conflicting instructions.
6. recommended_action: One allowed simulated action (RTH_EMERGENCY, HOVER_AND_DIAGNOSE, TELEMETRY_REFRESH_REQUEST, LAND_IMMEDIATE_SAFE, DISPATCH_INSPECTION_DRONE).
7. preconditions: List of operational conditions required before taking this action.
"""
