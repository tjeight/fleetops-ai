# FleetOps AI — API Reference & Examples

All requests communicate with the FastAPI backend at prefix `/api/v1`.

Interactive Swagger UI documentation is available at:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 1. System Health

### GET `/api/v1/health`
Checks backend service availability.
```bash
curl -X GET http://localhost:8000/api/v1/health
```
**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "fleetops-ai-backend",
  "version": "0.1.0"
}
```

### GET `/api/v1/ready`
Verifies database connectivity.
```bash
curl -X GET http://localhost:8000/api/v1/ready
```
**Response (200 OK):**
```json
{
  "status": "ready",
  "database": "connected"
}
```

---

## 2. Incidents API

### POST `/api/v1/incidents`
Intake a simulated drone incident. Idempotent when `idempotency_key` is supplied.
```bash
curl -X POST http://localhost:8000/api/v1/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": "SITE-ALPHA-01",
    "drone_id": "DRONE-04",
    "event_type": "BATTERY_CRITICAL",
    "severity": "HIGH",
    "idempotency_key": "webhook-sim-001",
    "telemetry_snapshot": {
      "battery_pct": 18.0,
      "altitude_m": 45.0,
      "speed_mps": 4.5,
      "gps_lat": 37.7745,
      "gps_lon": -122.4180,
      "timestamp": "2026-10-26T08:00:00Z",
      "heartbeat_ok": true
    },
    "mission_history": { "mission_name": "SOLAR_FARM_PATROL" },
    "device_health": { "notes": "battery cell 3 voltage sag" }
  }'
```
**Response (201 Created):**
```json
{
  "id": "inc-9481b7a2",
  "site_id": "SITE-ALPHA-01",
  "drone_id": "DRONE-04",
  "event_type": "BATTERY_CRITICAL",
  "severity": "HIGH",
  "status": "OPEN",
  "idempotency_key": "webhook-sim-001",
  "created_at": "2026-10-26T08:00:01Z",
  "updated_at": "2026-10-26T08:00:01Z",
  "investigations": [],
  "policy_decisions": [],
  "approval_requests": [],
  "simulated_actions": [],
  "audit_events": [
    {
      "actor": "system:api_gateway",
      "event_type": "INCIDENT_CREATED",
      "payload": { "severity": "HIGH", "event_type": "BATTERY_CRITICAL" },
      "timestamp": "2026-10-26T08:00:01Z"
    }
  ]
}
```

### POST `/api/v1/incidents/{id}/investigate`
Executes the stateful LangGraph investigation workflow.
```bash
curl -X POST http://localhost:8000/api/v1/incidents/inc-9481b7a2/investigate
```
**Response (200 OK):**
```json
{
  "id": "inc-9481b7a2",
  "status": "BLOCKED",
  "investigations": [
    {
      "likely_cause": "Critical low battery state (18.0% remaining capacity).",
      "diagnosis_category": "BATTERY_DEPLETION",
      "observed_facts": [
        "Drone battery capacity measured at 18.0%.",
        "Current altitude 45.0m, speed 4.5m/s."
      ],
      "hypotheses": ["Rapid cell discharge or mission duration exceeded energy budget."],
      "uncertainty_notes": "Battery discharge curve may steepen under headwind conditions.",
      "retrieved_sop_citations": [
        {
          "sop_id": "SOP-001",
          "title": "Drone Battery Reserve & Emergency Return Protocol",
          "relevance_score": 0.4128,
          "excerpt": "No drone shall be launched or re-tasked for a new patrol mission if remaining battery capacity is below 30.0%..."
        }
      ],
      "recommended_action": "RTH_EMERGENCY"
    }
  ],
  "policy_decisions": [
    {
      "action_type": "DISPATCH_INSPECTION_DRONE",
      "outcome": "BLOCK",
      "reasons": [
        "Battery capacity (18.0%) is below minimum required reserve (30.0%) for dispatch."
      ],
      "failed_checks": ["POL-BATTERY-01"],
      "policy_ids_evaluated": ["POL-ALLOWLIST-01", "POL-RAG-01", "POL-FRESHNESS-01", "POL-GEOFENCE-01", "POL-BATTERY-01"]
    }
  ]
}
```

### POST `/api/v1/incidents/{id}/approval`
Authorizes or rejects a pending simulated action.
```bash
curl -X POST http://localhost:8000/api/v1/incidents/inc-9481b7a2/approval \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "APPROVE",
    "operator_role": "demo_operator",
    "operator_id": "operator-01"
  }'
```

---

## 3. Scenarios API

### GET `/api/v1/scenarios`
Lists all 9 seeded evaluation scenarios.
```bash
curl -X GET http://localhost:8000/api/v1/scenarios
```

### POST `/api/v1/scenarios/run`
Executes an end-to-end scenario replay.
```bash
curl -X POST http://localhost:8000/api/v1/scenarios/run \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "low_battery"
  }'
```
**Response (200 OK):**
```json
{
  "scenario_id": "low_battery",
  "scenario_name": "1. Low Battery Threshold Violation",
  "expected_outcome": "BLOCKED",
  "actual_status": "BLOCKED",
  "expected_policy_decision": "BLOCK",
  "actual_policy_decision": "BLOCK",
  "matches_expected": true
}
```
