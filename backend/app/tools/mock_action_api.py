import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.policies.rules import ALLOWED_SIMULATED_ACTIONS


class MockActionExecutionError(Exception):
    pass


class MockActionTimeoutError(MockActionExecutionError):
    pass


class MockDroneActionAPI:
    """
    Simulation boundary for drone responses.
    Strictly simulated; connects to no physical drone hardware or flight controller.
    Enforces allowlist and provides realistic execution simulation.
    """
    def __init__(self):
        self._executed_idempotency_keys = set()

    async def execute_simulated_action(
        self,
        drone_id: str,
        site_id: str,
        action_type: str,
        action_params: Dict[str, Any],
        idempotency_key: str,
        simulate_timeout: bool = False
    ) -> Dict[str, Any]:
        # Validate action allowlist
        if action_type not in ALLOWED_SIMULATED_ACTIONS:
            raise MockActionExecutionError(f"Prohibited simulated action: {action_type}")

        # Check idempotency
        if idempotency_key in self._executed_idempotency_keys:
            raise MockActionExecutionError(
                f"Duplicate action execution detected for idempotency_key: {idempotency_key}"
            )

        # Simulate timeout for Scenario 7
        if simulate_timeout:
            # Simulate a bounded timeout failure
            await asyncio.sleep(0.05)
            raise MockActionTimeoutError(
                f"Communication timeout communicating with simulated drone telemetry bus for {drone_id}"
            )

        # Mark idempotency key
        self._executed_idempotency_keys.add(idempotency_key)

        # Generate realistic simulated execution telemetry result
        now_iso = datetime.now(timezone.utc).isoformat()
        
        if action_type == "RTH_EMERGENCY":
            result = {
                "status": "EXECUTED",
                "drone_id": drone_id,
                "command": "RTH_EMERGENCY",
                "flight_mode": "AUTO_RTH",
                "dock_coordinates": action_params.get("dock_coordinates", {"lat": 37.7750, "lon": -122.4150}),
                "estimated_arrival_seconds": 45,
                "executed_at": now_iso
            }
        elif action_type == "HOVER_AND_DIAGNOSE":
            result = {
                "status": "EXECUTED",
                "drone_id": drone_id,
                "command": "HOVER_AND_DIAGNOSE",
                "flight_mode": "POSITION_HOLD",
                "duration_seconds": action_params.get("duration_seconds", 30),
                "payload_bus_reset": "SUCCESS",
                "executed_at": now_iso
            }
        elif action_type == "TELEMETRY_REFRESH_REQUEST":
            result = {
                "status": "EXECUTED",
                "drone_id": drone_id,
                "command": "TELEMETRY_REFRESH_REQUEST",
                "ping_rtt_ms": 18,
                "refreshed_telemetry": {
                    "heartbeat": "ALIVE",
                    "signal_dbm": -68,
                    "last_ping_utc": now_iso
                },
                "executed_at": now_iso
            }
        elif action_type == "LAND_IMMEDIATE_SAFE":
            result = {
                "status": "EXECUTED",
                "drone_id": drone_id,
                "command": "LAND_IMMEDIATE_SAFE",
                "flight_mode": "AUTO_LAND",
                "descent_rate_mps": 1.2,
                "touchdown_expected_seconds": 15,
                "executed_at": now_iso
            }
        elif action_type == "DISPATCH_INSPECTION_DRONE":
            result = {
                "status": "EXECUTED",
                "drone_id": drone_id,
                "command": "DISPATCH_INSPECTION_DRONE",
                "flight_mode": "DISPATCH_STANDBY",
                "site_id": site_id,
                "target_perimeter": action_params.get("target_perimeter", "NORTH_SECTOR"),
                "assigned_backup_drone": "DRONE-BACKUP-02",
                "executed_at": now_iso
            }
        else:
            result = {
                "status": "EXECUTED",
                "drone_id": drone_id,
                "command": action_type,
                "executed_at": now_iso
            }

        return result


mock_action_api = MockDroneActionAPI()
