# FleetOps AI — Frontend Dashboard

Next.js 14 operations dashboard for Agentic Drone Incident Investigation and Safe Response.

## 1. Overview & Workflows

The FleetOps AI frontend provides site operators and drone engineers with:
- **Operations Dashboard (`/`)**: Aggregated incident counters, live fleet health roster, recent alarms, and quick scenario injection bar.
- **Incident List (`/incidents`)**: Filterable table by status (`OPEN`, `INVESTIGATING`, `AWAITING_APPROVAL`, `RESOLVED`, `BLOCKED`) and severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with search.
- **Incident Investigation Detail (`/incidents/[id]`)**: Full inspection view presenting:
  - Telemetry snapshots and data freshness indicators.
  - Stale telemetry alert banners.
  - Evidence-backed diagnosis with observed facts separated from hypotheses.
  - Uncertainty notes and procedural limitations.
  - ChromaDB SOP citations with relevance percentages.
  - Deterministic safety gate evaluation results and policy IDs.
  - Human approval dialog with role authorization testing (`demo_operator`, `supervisor`, `viewer`).
  - Chronological append-only audit trail with JSON payload inspectability.
- **Scenario Replay (`/scenarios`)**: One-click execution suite for all 9 predefined scenarios showing expected vs actual outcomes.

---

## 2. Technology Stack & Key Design Choices

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript (Strict Mode enabled)
- **Styling**: Tailwind CSS with custom aerospace theme (`#090d16` background, `#111726` surface)
- **Icons**: Lucide React
- **Testing**: Vitest + Testing Library + jsdom
- **API Architecture**: Typed REST client (`lib/api.ts`). No duplicate business logic in Next.js routes.

---

## 3. Directory Structure

```
frontend/
├── app/
│   ├── globals.css         # Tailwind directives & aerospace dark theme
│   ├── layout.tsx          # Root layout with sticky navbar & footer
│   ├── page.tsx            # Operations Dashboard
│   ├── incidents/
│   │   ├── page.tsx        # Incident List & Filters
│   │   └── [id]/page.tsx   # Detailed Investigation & Approval Interface
│   └── scenarios/
│       └── page.tsx        # Scenario Replay Suite
├── components/
│   ├── Navbar.tsx          # Top navigation bar
│   └── StatusBadge.tsx     # Status, Severity, and Policy outcome badges
├── lib/
│   ├── api.ts              # Typed FastAPI client with error handling
│   └── types.ts            # TypeScript interfaces
├── tests/
│   └── api_and_badges.test.ts # Vitest unit tests
├── .env.example
├── .env.local
├── package.json
└── tsconfig.json
```

---

## 4. Setup & Running Locally

### Prerequisites
- Node.js `20.x` or higher
- npm `10.x` or higher

### Installation
```bash
cd frontend
npm install
```

### Environment Configuration
Create `.env.local` from `.env.example`:
```bash
cp .env.example .env.local
```

| Variable | Purpose | Required | Safe Default |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of FastAPI backend API v1 | Yes | `http://localhost:8000/api/v1` |

### Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build & Start
```bash
npm run build
npm start
```

### Run Tests
```bash
npm test
```

### Type Checking & Linting
```bash
npm run type-check
npm run lint
```

---

## 5. Troubleshooting & FAQs

- **Backend Connection Alert**: Ensure FastAPI backend is running on `http://localhost:8000`. You can check readiness at `curl http://localhost:8000/api/v1/ready`.
- **CORS Issues**: The FastAPI backend includes `http://localhost:3000` in its `CORS_ORIGINS` setting by default. If running frontend on a different port, update `CORS_ORIGINS` in `backend/.env`.
