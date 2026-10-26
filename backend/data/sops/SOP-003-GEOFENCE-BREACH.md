# SOP-003: Airspace Geofence Containment & No-Fly Zones

## Document Information
- **Document ID**: SOP-003
- **Title**: Airspace Containment & Geofence Enforcement Protocol
- **Category**: Flight Safety & Navigation
- **Effective Date**: 2026-01-01
- **Version**: 3.1

## 1. Scope & Objective
Ensures strict compliance with FAA/EASA certified flight boundaries and site-specific exclusion zones.

## 2. Geofence Rules
- Drones operating within Site Alpha must remain strictly inside the operational bounding box:
  - Latitude: 37.7700°N to 37.7800°N
  - Longitude: -122.4200°W to -122.4100°W
- Any simulated or real target waypoint outside these bounds constitutes an Airspace Boundary Violation.

## 3. Enforcement
- Deterministic safety policies must unconditionally BLOCK any proposed waypoint or dispatch outside the certified polygon.
- Recommended remediation: `HOVER_AND_DIAGNOSE` or `RTH_EMERGENCY` back toward dock center (37.7750, -122.4150).
