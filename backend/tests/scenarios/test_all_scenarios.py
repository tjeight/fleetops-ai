import pytest
from httpx import AsyncClient
from app.services.scenario_catalog import get_seeded_scenarios


@pytest.mark.asyncio
async def test_scenario_catalog_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 9
    scenario_ids = [s["id"] for s in scenarios]
    expected_ids = [
        "low_battery",
        "stale_telemetry",
        "duplicate_webhook",
        "no_relevant_sop",
        "conflicting_sops",
        "unauthorized_operator",
        "tool_timeout",
        "geofence_violation",
        "normal_patrol_failure"
    ]
    for eid in expected_ids:
        assert eid in scenario_ids


@pytest.mark.parametrize("scenario", get_seeded_scenarios(), ids=lambda s: s["id"])
@pytest.mark.asyncio
async def test_run_each_scenario_end_to_end(client: AsyncClient, scenario):
    scenario_id = scenario["id"]
    res = await client.post("/api/v1/scenarios/run", json={"scenario_id": scenario_id})
    assert res.status_code == 200
    data = res.json()
    
    assert data["scenario_id"] == scenario_id
    assert data["matches_expected"] is True, f"Scenario {scenario_id} did not match expected outcome: {data}"
    
    if scenario_id == "low_battery":
        assert data["actual_policy_decision"] == "BLOCK"
        assert data["actual_status"] == "BLOCKED"
    elif scenario_id == "stale_telemetry":
        assert data["actual_policy_decision"] == "ALLOW"
        assert data["actual_status"] == "RESOLVED"
    elif scenario_id == "duplicate_webhook":
        assert data["actual_status"] == "RESOLVED"
    elif scenario_id == "no_relevant_sop":
        assert data["actual_policy_decision"] == "INSUFFICIENT_EVIDENCE"
        assert data["actual_status"] == "BLOCKED"
    elif scenario_id == "conflicting_sops":
        assert data["actual_policy_decision"] == "REQUIRES_APPROVAL"
        assert data["actual_status"] == "AWAITING_APPROVAL"
    elif scenario_id == "unauthorized_operator":
        assert data["unauthorized_auth_blocked"] is True
        assert "is not permitted" in str(data.get("auth_error_detail"))
    elif scenario_id == "tool_timeout":
        assert data["actual_status"] == "ERROR"
    elif scenario_id == "geofence_violation":
        assert data["actual_policy_decision"] == "BLOCK"
        assert data["actual_status"] == "BLOCKED"
    elif scenario_id == "normal_patrol_failure":
        assert data["actual_policy_decision"] == "ALLOW"
        assert data["actual_status"] == "RESOLVED"
