# FleetOps AI — Backend Service

FastAPI, LangGraph, ChromaDB, and PostgreSQL backend for Agentic Drone Incident Investigation and Safe Response.

## 1. Overview & Architecture

The FleetOps AI backend provides:
1. **Incident Intake Gateway**: Typed REST API with idempotency controls preventing duplicate incident ingestion or double execution.
2. **Stateful LangGraph Investigation**: Multi-node agent workflow for telemetry freshness validation, semantic SOP retrieval, diagnosis formulation, and safe response proposal.
3. **ChromaDB Vector Retrieval**: Semantic search across chunked drone Standard Operating Procedures (SOPs) with source citations and similarity scores.
4. **Deterministic Safety Policy Layer**: Pure Python safety gate enforcing allowlists, geofences, battery reserve limits, and operator permissions independently of the LLM.
5. **Human Approval Lifecycle**: Persistent pending approval state with backend role authorization (`demo_operator`, `supervisor`, `viewer`) and pre-execution safety revalidation.
6. **Mock Action Boundary**: Safe simulator executing predefined harmless commands (`RTH_EMERGENCY`, `HOVER_AND_DIAGNOSE`, `TELEMETRY_REFRESH_REQUEST`, `LAND_IMMEDIATE_SAFE`, `DISPATCH_INSPECTION_DRONE`). Never connects to real drone hardware.

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── api/v1/             # REST API routers (incidents, scenarios, dashboard, health)
│   ├── core/               # Configuration (Pydantic Settings) & Async DB engine
│   ├── schemas/            # Typed Pydantic request/response models
│   ├── models/             # SQLAlchemy 2.0 ORM entities
│   ├── services/           # Incident orchestration & scenario catalog
│   ├── agents/             # LangGraph state graph & prompt templates
│   ├── retrieval/          # ChromaDB persistent store & SOP ingestion
│   ├── policies/           # Deterministic Python safety gate
│   ├── tools/              # Harmless mock drone action simulator
│   ├── db/                 # Database seeding scripts
│   └── main.py             # FastAPI entrypoint & lifespan lifecycle
├── tests/
│   ├── unit/               # Policy rules and retrieval unit tests
│   ├── integration/        # API endpoints & idempotency tests
│   └── scenarios/          # End-to-end tests for all 9 scenarios
├── data/
│   ├── sops/               # Synthetic drone Standard Operating Procedures (.md)
│   └── scenarios/          # Seeded scenario fixtures
├── alembic/                # Database migrations
├── pyproject.toml          # Python dependencies & Ruff/Pytest configuration
└── README.md
```

---

## 3. Supported Python Version & Setup

- **Supported Python**: `Python 3.11+` (tested on 3.11.13 and 3.12.3)
- **Package Manager**: `uv` or `pip`

### Virtual Environment Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies using uv (recommended for speed) or pip
uv pip install -e ".[dev]"
# Or: pip install -e ".[dev]"
```

---

## 4. Environment Variables (`.env`)

Create `.env` from `.env.example`:
```bash
cp .env.example .env
```

| Variable | Purpose | Required | Safe Default |
|---|---|---|---|
| `APP_ENV` | Application environment (`development` / `production`) | No | `development` |
| `DATABASE_URL` | SQLAlchemy async database connection URL | Yes | `sqlite+aiosqlite:///./fleetops.db` |
| `CHROMA_PERSIST_DIRECTORY` | Persistent vector store directory | Yes | `./chroma_data` |
| `EMBEDDING_PROVIDER` | Embedding function (`default` / `chroma` / `openai`) | No | `default` (deterministic offline) |
| `OPENAI_API_KEY` | Optional OpenAI key for live LLM reasoning | No | `""` (offline deterministic fallback active) |
| `OPENAI_MODEL` | OpenAI model identifier | No | `gpt-4o-mini` |
| `LANGFUSE_PUBLIC_KEY` | Optional Langfuse tracing public key | No | `""` (graceful degradation) |
| `CORS_ORIGINS` | Permitted browser origins | No | `http://localhost:3000,http://127.0.0.1:3000` |
| `LOG_LEVEL` | Logging verbosity | No | `INFO` |

---

## 5. Database Migrations & Initial Seeding

### Apply Alembic Migrations
```bash
alembic upgrade head
```

### Ingest SOP Documents into ChromaDB
```bash
python -m app.retrieval.ingest
```

### Seed Initial Demonstration Incidents
```bash
python -m app.db.seed
```

---

## 6. Running the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Base: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 7. Testing

### Run All 23 Automated Tests
```bash
pytest -v
```

### Run Policy Gate Unit Tests
```bash
pytest tests/unit/test_policy_rules.py -v
```

### Run Scenario Replay Tests (All 9 Mandatory Scenarios)
```bash
pytest tests/scenarios/test_all_scenarios.py -v
```

---

## 8. 9 Mandatory Seeded Scenarios

1. `low_battery`: Drone battery 18% crosses minimum reserve threshold (<30%). Safety gate blocks dispatch.
2. `stale_telemetry`: Telemetry older than 60s is detected; flight commands blocked, refresh requested.
3. `duplicate_webhook`: Submitting duplicate idempotency key returns existing incident; prevents duplicate actions.
4. `no_relevant_sop`: Unknown anomaly returns zero ChromaDB citations; flags `INSUFFICIENT_EVIDENCE`.
5. `conflicting_sops`: Extreme weather alarm retrieves conflicting SOP-005 directives; enters `AWAITING_APPROVAL`.
6. `unauthorized_operator`: Operator with role `viewer` attempting approval is rejected with HTTP 403 Forbidden.
7. `tool_timeout`: Simulated telemetry API timeout preserves workflow state without crashing.
8. `geofence_violation`: Target coordinates outside operational bounding box are blocked by `POL-GEOFENCE-01`.
9. `normal_patrol_failure`: Optical gimbal fault diagnosed; SOP-004 cited; safe diagnostic hover executed.
