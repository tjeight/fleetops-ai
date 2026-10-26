from datetime import datetime, timezone, timedelta
from app.policies.rules import evaluate_safety_policy


def test_policy_allowlist_blocks_unauthorized_flight_command():
    now_utc = datetime.now(timezone.utc)
    result = evaluate_safety_policy(
        proposed_action="TAKEOFF_ARM_AND_FLY_UNRESTRICTED",
        action_params={},
        telemetry={"battery_pct": 80.0, "timestamp": now_utc.isoformat()},
        incident_timestamp=now_utc,
        citations_count=2
    )
    assert result.outcome == "BLOCK"
    assert "POL-ALLOWLIST-01" in result.failed_checks


def test_policy_blocks_dispatch_when_battery_below_reserve():
    now_utc = datetime.now(timezone.utc)
    result = evaluate_safety_policy(
        proposed_action="DISPATCH_INSPECTION_DRONE",
        action_params={},
        telemetry={"battery_pct": 18.0, "timestamp": now_utc.isoformat(), "gps_lat": 37.775, "gps_lon": -122.415},
        incident_timestamp=now_utc,
        citations_count=1
    )
    assert result.outcome == "BLOCK"
    assert "POL-BATTERY-01" in result.failed_checks
    assert any("below minimum required reserve" in r for r in result.reasons)


def test_policy_blocks_flight_action_on_stale_telemetry():
    now_utc = datetime.now(timezone.utc)
    stale_time = now_utc - timedelta(seconds=240)
    result = evaluate_safety_policy(
        proposed_action="RTH_EMERGENCY",
        action_params={},
        telemetry={"battery_pct": 50.0, "timestamp": stale_time.isoformat(), "gps_lat": 37.775, "gps_lon": -122.415},
        incident_timestamp=now_utc,
        citations_count=1
    )
    assert result.outcome == "BLOCK"
    assert "POL-FRESHNESS-01" in result.failed_checks


def test_policy_allows_telemetry_refresh_request_even_if_stale():
    now_utc = datetime.now(timezone.utc)
    stale_time = now_utc - timedelta(seconds=120)
    result = evaluate_safety_policy(
        proposed_action="TELEMETRY_REFRESH_REQUEST",
        action_params={},
        telemetry={"battery_pct": 60.0, "timestamp": stale_time.isoformat(), "gps_lat": 37.775, "gps_lon": -122.415},
        incident_timestamp=now_utc,
        citations_count=1
    )
    assert result.outcome == "ALLOW"


def test_policy_blocks_geofence_violation():
    now_utc = datetime.now(timezone.utc)
    # Outside bounding box (lat > 37.7800)
    result = evaluate_safety_policy(
        proposed_action="RTH_EMERGENCY",
        action_params={"target_lat": 37.8100, "target_lon": -122.4150},
        telemetry={"battery_pct": 70.0, "timestamp": now_utc.isoformat(), "gps_lat": 37.775, "gps_lon": -122.415},
        incident_timestamp=now_utc,
        citations_count=1
    )
    assert result.outcome == "BLOCK"
    assert "POL-GEOFENCE-01" in result.failed_checks


def test_policy_requires_human_approval_for_sensitive_dispatch():
    now_utc = datetime.now(timezone.utc)
    result = evaluate_safety_policy(
        proposed_action="DISPATCH_INSPECTION_DRONE",
        action_params={},
        telemetry={"battery_pct": 75.0, "timestamp": now_utc.isoformat(), "gps_lat": 37.775, "gps_lon": -122.415},
        incident_timestamp=now_utc,
        citations_count=1
    )
    assert result.outcome == "REQUIRES_APPROVAL"
    assert "POL-APPROVAL-01" in result.policy_ids_evaluated


def test_policy_blocks_viewer_role_from_execution():
    now_utc = datetime.now(timezone.utc)
    result = evaluate_safety_policy(
        proposed_action="HOVER_AND_DIAGNOSE",
        action_params={},
        telemetry={"battery_pct": 75.0, "timestamp": now_utc.isoformat(), "gps_lat": 37.775, "gps_lon": -122.415},
        incident_timestamp=now_utc,
        citations_count=1,
        operator_role="viewer"
    )
    assert result.outcome == "BLOCK"
    assert "POL-AUTH-01" in result.failed_checks
