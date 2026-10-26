# FleetOps AI Architecture & System Design

FleetOps AI is a production-grade, simulated agentic drone incident investigation and deterministic safe response platform.

## 1. System Overview & Core Philosophy

In industrial and autonomous drone operations, incidents require rapid analysis across heterogeneous streams: telemetry heartbeats, hardware diagnostic logs, mission logs, and standard operating procedures (SOPs).

A core engineering principle guides FleetOps AI:
> **"The AI Proposes and Explains; Deterministic Code Validates and Enforces."**

Large Language Models (LLMs) and agentic workflows excel at correlating unstructured evidence and identifying potential explanations. However, in safety-critical aviation domains, an LLM must **never** be the sovereign authority executing flight commands. FleetOps AI enforces an independent, deterministic Python safety gate that intercepts every proposed action and evaluates hard constraints (geofence polygons, battery reserve thresholds, telemetry age limits, and operator permissions) before any simulated action can execute.

```mermaid
flowchart TD
    subgraph Intake["1. Incident Ingestion"]
        A[Site Sensor / Webhook Alarm] -->|POST /api/v1/incidents| B[FastAPI Gateway]
        B --> C{Idempotency Check}
        C -->|Duplicate Key| D[Return Existing Record]
        C -->|New Key| E[(PostgreSQL / SQLite)]
    end

    subgraph AgenticWorkflow["2. Stateful LangGraph Investigation"]
        E --> F[intake_validator]
        F --> G[freshness_checker]
        G --> H[retrieve_sops]
        H -->|Query Embeddings| I[(ChromaDB SOP Store)]
        I -->|Citations + Metadata| H
        H --> J[synthesize_diagnosis]
        J --> K[propose_recommended_action]
    end

    subgraph SafetyGate["3. Deterministic Safety Enforcement"]
        K --> L[evaluate_safety_policy]
        L --> M{Deterministic Gate}
        M -->|ALLOW| N[mock_action_executor]
        M -->|REQUIRES_APPROVAL| O[Pause Graph: Awaiting Operator]
        M -->|BLOCK| P[Mark BLOCKED + Log Reason]
        M -->|INSUFFICIENT_EVIDENCE| Q[Mark BLOCKED + Flag Missing Data]
    end

    subgraph HumanInTheLoop["4. Human Approval Interface"]
        O --> R[Next.js Operator Dashboard]
        R -->|POST /api/v1/incidents/:id/approval| S[Backend Authorization Check]
        S -->|Role == viewer| T[HTTP 403 Forbidden]
        S -->|Role in demo_operator, supervisor| U[Revalidate Safety Policies]
        U -->|Passed| N
        U -->|Failed| P
    end

    subgraph ExecutionAudit["5. Simulation & Audit Log"]
        N --> V[Harmless Mock Action API]
        V --> W[(Append-Only Audit Log)]
        P --> W
        W --> X[Next.js Live Dashboard]
    end
```

---

## 2. Component Boundaries

### A. Frontend Layer (Next.js 14 App Router)
- **Role**: Operator UI, telemetry visualization, incident triage, and human approval portal.
- **Tech**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide icons.
- **Boundary**: Communicates strictly with the FastAPI REST API via typed HTTP client (`lib/api.ts`). No backend logic or database access occurs in Next.js routes.

### B. API Gateway & Orchestration (FastAPI + LangGraph)
- **Role**: Endpoint routing, request validation via Pydantic v2, asynchronous workflow orchestration.
- **Tech**: FastAPI, Pydantic, LangGraph StateGraph, MemorySaver checkpointer.
- **Boundary**: Coordinates data loading, triggers graph transitions, and manages persistent incident states.

### C. RAG Vector Retrieval Store (ChromaDB)
- **Role**: Semantic procedure chunk storage and retrieval with source citations.
- **Tech**: ChromaDB PersistentClient, Deterministic Drone SOP Embedding Function (384-dimensional normalized vector hashing with cosine similarity).
- **Boundary**: Provides grounded procedure excerpts (`SOP-001` through `SOP-005`). Returns empty citations when no procedure exists, preventing LLM hallucination.

### D. Deterministic Safety Gate (`app/policies/rules.py`)
- **Role**: Pure Python validation gate completely decoupled from LLMs.
- **Tech**: Deterministic rule engine evaluating:
  1. `POL-ALLOWLIST-01`: Action in harmless allowlist.
  2. `POL-BATTERY-01`: Minimum 30% battery for dispatch.
  3. `POL-FRESHNESS-01`: Maximum 60s telemetry age.
  4. `POL-GEOFENCE-01`: Containment within Site Alpha operational bounding box.
  5. `POL-RAG-01`: Mandatory procedure evidence grounding.
  6. `POL-CONFLICT-01`: Mandatory supervisor escalation on contradictory SOPs.
  7. `POL-AUTH-01`: Role-based access control (`viewer` role rejected with 403).
  8. `POL-APPROVAL-01`: Mandatory operator authorization on high-consequence dispatches.

### E. Persistence Layer (PostgreSQL & SQLite)
- **Role**: Relational storage for incidents, investigation findings, policy decisions, approvals, and audit events.
- **Tech**: SQLAlchemy 2.0 (asyncio with `asyncpg` and `aiosqlite`), Alembic migrations.

---

## 3. Data Schema & Relationships

```mermaid
erDiagram
    INCIDENTS ||--o{ INVESTIGATIONS : has
    INCIDENTS ||--o{ POLICY_DECISIONS : has
    INCIDENTS ||--o{ APPROVAL_REQUESTS : has
    INCIDENTS ||--o{ SIMULATED_ACTIONS : has
    INCIDENTS ||--o{ AUDIT_EVENTS : records

    INCIDENTS {
        string id PK
        string site_id
        string drone_id
        string event_type
        string severity
        string status
        string idempotency_key UK
        json telemetry_snapshot
        json mission_history
        json device_health
        datetime created_at
        datetime updated_at
    }

    INVESTIGATIONS {
        string id PK
        string incident_id FK
        string status
        string likely_cause
        string diagnosis_category
        json observed_facts
        json hypotheses
        string uncertainty_notes
        json retrieved_sop_citations
        string recommended_action
        json recommended_action_params
        json preconditions
        datetime created_at
    }

    POLICY_DECISIONS {
        string id PK
        string incident_id FK
        string investigation_id FK
        string action_type
        string outcome
        json reasons
        json failed_checks
        json policy_ids_evaluated
        datetime evaluated_at
    }

    APPROVAL_REQUESTS {
        string id PK
        string incident_id FK
        string action_type
        json action_params
        string status
        datetime requested_at
        datetime resolved_at
        string resolved_by
        string operator_role
        string rejection_reason
    }

    SIMULATED_ACTIONS {
        string id PK
        string incident_id FK
        string action_type
        json action_params
        string idempotency_key UK
        string status
        datetime executed_at
        json mock_result
    }

    AUDIT_EVENTS {
        string id PK
        string incident_id FK
        string actor
        string event_type
        json payload
        datetime timestamp
    }
```
