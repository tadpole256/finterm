# Roadmap

## Status Summary

- Phase 1: **Completed**
- Phase 2: **Completed**
- Phase 3: **Completed (MVP)**
- Phase 4: **Completed (MVP)**
- Phase 5: **Completed (MVP)**
- Phase 6+: **Not started**

## Phase Plan

### Phase 1: Foundation (Completed)

- Monorepo scaffold (`apps/web`, `apps/api`, `apps/worker`, `infra`, docs)
- Tooling baseline: lint/typecheck/tests for web and API
- Baseline schema + Alembic migration for core entities
- Seed pipeline with deterministic mock fixtures
- Dark-theme UI shell and navigation
- Required docs created (`README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `TODO.md`)
- Note: migration/seed command path is implemented; execution requires local PostgreSQL to be running.

### Phase 2: Core Market Workspace (Completed)

- Provider abstraction + mock provider implementation
- Caching service with Redis/in-memory fallback
- Market/dashboard APIs
- Watchlist CRUD + reorder APIs
- Security workspace API payload with technical indicators
- Dashboard, Watchlists, Security Workspace screens
- Charting with candlesticks, volume, SMA/EMA overlays, RSI, MACD panes
- Basic screening API endpoint and service

### Phase 3: Research & Notes (Completed - MVP)

- Research note CRUD + search APIs (`/research/notes`) and notebook UI (`/research`)
- Thesis CRUD APIs and notebook thesis management
- Theme lookup endpoint (`/research/themes`)
- Note synthesis endpoint (`/research/synthesis`) plus AI alias (`/ai/note-synthesis`)
- Heuristic synthesis engine for thesis/open questions/risks/next-watch outputs
- Research route and synthesis test coverage

### Phase 4: Portfolio (Completed - MVP)

- Portfolio routes:
  - `GET /api/v1/portfolio/overview`
  - `GET /api/v1/portfolio/positions`
  - `GET /api/v1/portfolio/transactions`
  - `POST /api/v1/portfolio/transactions`
  - `DELETE /api/v1/portfolio/transactions/{transaction_id}`
- Deterministic portfolio transaction seeding and position recomputation logic.
- Cost basis + realized/unrealized P&L calculations with sector exposure rollups.
- Portfolio workspace (`/portfolio`) with holdings table, exposure panel, transaction entry/delete, and artifact linkage (watchlists + notes/thesis counts).
- Added portfolio service and math test coverage.

### Phase 5: Alerts & Briefs (Completed - MVP)

- Alert routes:
  - `GET /api/v1/alerts`
  - `POST /api/v1/alerts`
  - `PATCH /api/v1/alerts/{alert_id}`
  - `DELETE /api/v1/alerts/{alert_id}`
  - `GET /api/v1/alerts/events`
  - `POST /api/v1/alerts/evaluate`
- Notification routes:
  - `GET /api/v1/notifications`
  - `PATCH /api/v1/notifications/{notification_id}/read`
- Brief routes:
  - `GET /api/v1/briefs/latest`
  - `POST /api/v1/briefs/generate`
- Worker tick executes alert-rule evaluation and once-per-day brief generation.
- Alerts workspace (`/alerts`) added to UI for alert management, event review, notification read-state, and brief generation.
- Added backend and frontend tests for Phase 5 flows.

### Phase 6: Filings & Macro (Pending)

- SEC adapter ingestion pipeline
- Filing diff/change detection logic
- Expanded macro time-series integration

### Phase 7: Screener & Polish (Pending)

- Saved screens UI
- richer filtering UX
- keyboard navigation and interaction polish

## Risks and Mitigations

- **Data entitlements/legal ambiguity**
  - Mitigation: maintain provider adapters and explicit legal/data documentation.
- **Provider outages/degraded local services**
  - Mitigation: cache fallback path + stale/degraded UI indicators.
- **Scope creep beyond personal MVP**
  - Mitigation: strict phased execution with TODO gating.

## Data Provider Strategy

1. Mock provider (current)
2. Delayed/basic provider adapter
3. Premium provider adapter with entitlement-aware fields
4. Optional broker-connected provider for account-linked flows

## Broker Integration Notes (Future)

- Keep broker adapters separate from market data adapters.
- Add broker permissions, symbol mapping, and reconciliation layer in Phase 4/5+.
- Avoid coupling order/execution concerns into current read-first workspace domains.
