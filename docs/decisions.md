# Architecture Decision Records (ADR)

## ADR 001: Next.js App Router for Dashboard Interface
- **Context**: The original project blueprint suggested Streamlit. The user selected Next.js.
- **Decision**: Adopt Next.js 14 with App Router, TypeScript, and Tailwind CSS.
- **Consequences**:
  - Provides a production-grade operations experience with tabbed views, responsive layouts, and interactive approval flows.
  - Keeps business logic strictly on the Python backend; Next.js serves purely as a typed API client.
  - Zero state leakage between client and server.

## ADR 002: Deterministic Python Safety Gate Decoupled from LLM
- **Context**: In autonomous drone missions, LLMs may produce unpredictable or hallucinations regarding flight actions.
- **Decision**: Isolate safety policy evaluation into pure Python functions (`app/policies/rules.py`).
- **Consequences**:
  - The LLM only proposes and explains recommendations.
  - The deterministic gate evaluates hard constraints (geofence boundaries, battery thresholds, telemetry freshness, allowlist) independently.
  - Even if an LLM strongly suggests dispatching a drone into an exclusion zone or with 10% battery, the safety gate unconditionally blocks execution (`BLOCK`).

## ADR 003: 100% Offline Deterministic Embedding & Evaluation Strategy
- **Context**: Portfolio evaluators or automated CI environments frequently lack paid external OpenAI or third-party vector store credentials.
- **Decision**: Implement a deterministic 384-dimensional feature vector hashing embedding function and structured offline synthesizer.
- **Consequences**:
  - The entire test suite and scenario suite runs 100% offline in ~2 seconds without API keys.
  - If `OPENAI_API_KEY` is supplied, live LLM reasoning is enabled seamlessly.
  - Ground truth for all 9 scenarios is verifiable and deterministic.

## ADR 004: Dual Async Engine Support (PostgreSQL & SQLite)
- **Context**: Developers need rapid local iteration without requiring PostgreSQL installed on their host, while Docker and production deployments require persistent PostgreSQL.
- **Decision**: Configure SQLAlchemy 2.0 with async engine support for both `postgresql+asyncpg` and `sqlite+aiosqlite`.
- **Consequences**:
  - Zero setup friction for local pytest runs and developers.
  - Docker Compose uses dedicated PostgreSQL 16 container on port 5434.

## ADR 005: Separate Docker Compose Stack with Non-Conflicting Ports
- **Context**: The host machine may already run a system PostgreSQL service on standard port 5432.
- **Decision**: Configure Docker Compose with host port `5434:5432` for `postgres`, `8000:8000` for `backend`, and `3000:3000` for `frontend`.
- **Consequences**:
  - Eliminates port collision risks on the user's host machine.
  - Fully isolated container network (`fleetops-network`).
