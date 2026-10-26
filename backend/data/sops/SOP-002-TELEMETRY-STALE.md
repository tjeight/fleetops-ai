# SOP-002: Telemetry Desynchronization & Stale Data Protocol

## Document Information
- **Document ID**: SOP-002
- **Title**: Telemetry Staleness and Communication Loss Response
- **Category**: Avionics & Communications
- **Effective Date**: 2026-01-01
- **Version**: 1.8

## 1. Scope & Objective
Defines protocol requirements when telemetry feeds, GPS pings, or avionics health heartbeats are delayed, intermittent, or missing during an incident.

## 2. Staleness Thresholds
- **Telemetry Age Limit**: Any telemetry packet older than 60 seconds relative to incident intake timestamp is classified as STALE.
- **Missing Telemetry**: Absence of GPS coordinates or battery percentage constitutes INCOMPLETE_EVIDENCE.

## 3. Mandatory Safety Restrictions
- Under no circumstances shall an autonomous flight movement or dispatch action be executed based on stale telemetry data.
- The investigation engine must flag `STALE_TELEMETRY_DETECTED` and set uncertainty notes accordingly.
- The only permitted immediate action is `TELEMETRY_REFRESH_REQUEST` to poll the onboard flight controller via redundant cellular/radio link.
