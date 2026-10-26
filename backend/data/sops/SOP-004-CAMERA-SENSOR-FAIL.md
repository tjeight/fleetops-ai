# SOP-004: Optical Sensor Failure & Patrol Malfunction

## Document Information
- **Document ID**: SOP-004
- **Title**: Camera & Optical Sensor Fault Resolution During Patrol
- **Category**: Payload & Inspection
- **Effective Date**: 2026-01-01
- **Version**: 1.5

## 1. Scope & Objective
Applies to perimeter patrol failures caused by primary camera sensor glitch, optical gimbal lock, or feed freeze.

## 2. Diagnostics
- If battery level is healthy (> 50%) and telemetry is fresh (< 30s), assess sensor hardware metrics.
- Check motor temperature and vibration indices.
- If vibration is normal and error is confined to the optical sensor payload:

## 3. Recommended Procedure
- Step 1: Issue `HOVER_AND_DIAGNOSE` for 30 seconds to attempt payload bus reset.
- Step 2: If telemetry remains stable, initiate `RTH_EMERGENCY` for bench diagnostic and inspection at primary charging pad.
