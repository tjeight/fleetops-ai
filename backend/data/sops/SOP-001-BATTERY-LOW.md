# SOP-001: Low Battery Emergency and Reserve Policy

## Document Information
- **Document ID**: SOP-001
- **Title**: Drone Battery Reserve & Emergency Return Protocol
- **Category**: Power & Propulsion
- **Effective Date**: 2026-01-01
- **Version**: 2.4

## 1. Scope & Objective
This procedure establishes mandatory flight thresholds and emergency responses for multi-rotor industrial drones experiencing battery degradation or low charge states during autonomous or manual missions.

## 2. Reserve Thresholds & Prohibitions
- **Minimum Dispatch Reserve**: No drone shall be launched or re-tasked for a new patrol mission if remaining battery capacity is below 30.0%.
- **Return to Home (RTH) Trigger**: If battery capacity drops below 25.0% during an active mission, the system must trigger an immediate RTH command to the nearest authorized charging dock.
- **Critical Landing Threshold**: If battery capacity reaches or falls below 15.0%, the drone is strictly prohibited from continuing cruise flight and must initiate an immediate safe descent and landing at its current GPS location.

## 3. Autonomous Decision Logic
When a battery anomaly or low-voltage warning is detected:
1. Verify telemetry timestamp to confirm battery percentage freshness.
2. If battery is <= 30.0%, any dispatch recommendation MUST BE BLOCKED by safety policies.
3. Formulate recommendation: `RTH_EMERGENCY` with dock coordinates, or `LAND_IMMEDIATE_SAFE` if critical.
