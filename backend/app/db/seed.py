import asyncio
from datetime import datetime, timezone, timedelta
from app.core.database import AsyncSessionLocal, init_db
from app.services.incident_service import IncidentService
from app.schemas.incident import IncidentCreate
from app.retrieval.chroma_store import retriever
import os

async def seed_data():
    print("[Seed] Initializing database...")
    await init_db()

    # Ingest SOPs
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sop_dir = os.path.join(base_dir, "data", "sops")
    if os.path.exists(sop_dir):
        print(f"[Seed] Ingesting SOPs from {sop_dir}...")
        count = retriever.ingest_sop_directory(sop_dir)
        print(f"[Seed] Ingested {count} chunks.")

    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.isoformat()

    sample_incidents = [
        {
            "site_id": "SITE-ALPHA-01",
            "drone_id": "DRONE-04",
            "event_type": "SENSOR_FAILURE",
            "severity": "MEDIUM",
            "idempotency_key": "seed-incident-001",
            "telemetry_snapshot": {
                "battery_pct": 74.0,
                "altitude_m": 42.0,
                "speed_mps": 4.8,
                "gps_lat": 37.7751,
                "gps_lon": -122.4162,
                "timestamp": now_iso,
                "heartbeat_ok": True
            },
            "mission_history": {"mission_name": "PERIMETER_SURVEILLANCE_ROUTINE"},
            "device_health": {"camera_status": "PAYLOAD_BUS_ERROR", "vibration_level": "NORMAL"}
        },
        {
            "site_id": "SITE-ALPHA-01",
            "drone_id": "DRONE-02",
            "event_type": "HIGH_WIND_PERIMETER_BREACH",
            "severity": "HIGH",
            "idempotency_key": "seed-incident-002",
            "telemetry_snapshot": {
                "battery_pct": 78.0,
                "altitude_m": 30.0,
                "speed_mps": 6.5,
                "gps_lat": 37.7760,
                "gps_lon": -122.4130,
                "timestamp": now_iso,
                "heartbeat_ok": True
            },
            "mission_history": {"mission_name": "PERIMETER_EAST_GUARD"},
            "device_health": {"notes": "wind sensor gust 18 m/s, fence alarm"}
        },
        {
            "site_id": "SITE-ALPHA-01",
            "drone_id": "DRONE-03",
            "event_type": "BATTERY_CRITICAL",
            "severity": "HIGH",
            "idempotency_key": "seed-incident-003",
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
    ]

    async with AsyncSessionLocal() as db:
        for inc_data in sample_incidents:
            inc = await IncidentService.create_incident(IncidentCreate(**inc_data), db)
            print(f"[Seed] Created incident: {inc.id} ({inc.event_type})")
            
            # Run investigation for seed incident 1
            if inc.idempotency_key == "seed-incident-001":
                print(f"[Seed] Investigating {inc.id}...")
                inv = await IncidentService.run_investigation(inc.id, db)
                print(f"[Seed] Incident {inv.id} investigated. Status: {inv.status}")

            # Run investigation for seed incident 2 (which will enter AWAITING_APPROVAL)
            if inc.idempotency_key == "seed-incident-002":
                print(f"[Seed] Investigating {inc.id} (should await approval)...")
                inv = await IncidentService.run_investigation(inc.id, db)
                print(f"[Seed] Incident {inv.id} investigated. Status: {inv.status}")

    print("[Seed] Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
