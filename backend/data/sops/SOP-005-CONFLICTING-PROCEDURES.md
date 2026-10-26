# SOP-005: High-Wind Perimeter Alarm Protocols (Conflicting Directives)

## Document Information
- **Document ID**: SOP-005
- **Title**: High-Wind Perimeter Security Breach Response (Dual Directive)
- **Category**: Security & Extreme Weather
- **Effective Date**: 2026-01-01
- **Version**: 2.0-CONFLICT

## 1. Scope & Objective
Applies when a perimeter fence alarm triggers simultaneously with gusts exceeding 15 m/s.

## 2. Contradictory Operational Directives
- **Directive A (Tactical Security)**: Drone must ascend to 100m AGL immediately to maintain optical visual coverage over the perimeter boundary and track potential intruders.
- **Directive B (Aeronautical Safety)**: Under wind speeds exceeding 15 m/s, drone must immediately descend below 15m AGL and hover near shelter to avoid structural aerodynamic failure.

## 3. Mandatory Human Approval Resolution
- Because Directives A and B present an irreconcilable conflict between security coverage and flight airworthiness, automated execution is strictly prohibited.
- The investigation engine MUST surface procedural conflict in uncertainty notes and return policy outcome `REQUIRES_APPROVAL`.
- An authorized human flight supervisor must review wind telemetry and make the final decision before any simulated movement.
