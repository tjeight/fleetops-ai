import pytest
from httpx import AsyncClient
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_health_and_ready_endpoints(client: AsyncClient):
    res_health = await client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_ready = await client.get("/api/v1/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_incident_intake_idempotency(client: AsyncClient):
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "site_id": "SITE-ALPHA-01",
        "drone_id": "DRONE-01",
        "event_type": "SENSOR_FAILURE",
        "severity": "LOW",
        "idempotency_key": "idemp-webhook-12345",
        "telemetry_snapshot": {
            "battery_pct": 80.0,
            "gps_lat": 37.775,
            "gps_lon": -122.415,
            "timestamp": now_iso
        }
    }

    # 1st Intake
    res1 = await client.post("/api/v1/incidents", json=payload)
    assert res1.status_code == 201
    data1 = res1.json()
    incident_id1 = data1["id"]

    # 2nd Intake with same idempotency key
    res2 = await client.post("/api/v1/incidents", json=payload)
    assert res2.status_code == 201
    data2 = res2.json()
    
    # Must return the identical incident ID
    assert data2["id"] == incident_id1


@pytest.mark.asyncio
async def test_investigation_and_approval_workflow(client: AsyncClient):
    now_iso = datetime.now(timezone.utc).isoformat()
    # High wind perimeter breach triggers conflicting SOPs and requires approval
    payload = {
        "site_id": "SITE-ALPHA-01",
        "drone_id": "DRONE-02",
        "event_type": "HIGH_WIND_PERIMETER_BREACH",
        "severity": "HIGH",
        "telemetry_snapshot": {
            "battery_pct": 75.0,
            "altitude_m": 25.0,
            "speed_mps": 6.0,
            "gps_lat": 37.7760,
            "gps_lon": -122.4130,
            "timestamp": now_iso,
            "heartbeat_ok": True
        },
        "device_health": {"notes": "wind gust 17 m/s"}
    }

    # Create incident
    create_res = await client.post("/api/v1/incidents", json=payload)
    assert create_res.status_code == 201
    inc_id = create_res.json()["id"]

    # Trigger investigation
    inv_res = await client.post(f"/api/v1/incidents/{inc_id}/investigate")
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert inv_data["status"] == "AWAITING_APPROVAL"
    assert len(inv_data["approval_requests"]) == 1
    assert inv_data["approval_requests"][0]["status"] == "PENDING"

    # Unauthorized operator attempt (viewer)
    unauth_res = await client.post(
        f"/api/v1/incidents/{inc_id}/approval",
        json={
            "decision": "APPROVE",
            "operator_role": "viewer",
            "operator_id": "viewer-01"
        }
    )
    assert unauth_res.status_code == 403

    # Authorized operator approval (demo_operator)
    auth_res = await client.post(
        f"/api/v1/incidents/{inc_id}/approval",
        json={
            "decision": "APPROVE",
            "operator_role": "demo_operator",
            "operator_id": "operator-01"
        }
    )
    assert auth_res.status_code == 200
    resolved_data = auth_res.json()
    assert resolved_data["status"] == "RESOLVED"
    assert len(resolved_data["simulated_actions"]) == 1
    assert resolved_data["simulated_actions"][0]["status"] == "EXECUTED"

    # Verify audit events
    audit_res = await client.get(f"/api/v1/incidents/{inc_id}/audit")
    assert audit_res.status_code == 200
    events = audit_res.json()
    assert len(events) >= 4
    event_types = [e["event_type"] for e in events]
    assert "INCIDENT_CREATED" in event_types
    assert "APPROVAL_REQUESTED" in event_types
    assert "APPROVAL_RESOLVED" in event_types
