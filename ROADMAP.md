# Roadmap

## Status Summary

- Phase 1: **Completed**
- Phase 2: **Completed**
- Phase 3: **Completed (MVP)**
- Phase 4: **Completed (MVP)**
- Phase 5: **Completed (MVP)**
- Phase 6: **Completed (MVP)**
- Phase 7: **Completed (MVP)**
- Phase 8: **Completed (MVP)**
- Phase 9+: **Not started**

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

### Phase 6: Filings & Macro (Completed - MVP)

- Filings adapter + sync:
  - `POST /api/v1/filings/sync`
  - `GET /api/v1/filings`
  - `GET /api/v1/filings/{filing_id}`
- Macro adapter + sync:
  - `POST /api/v1/macro/sync`
  - `GET /api/v1/macro/series`
  - `GET /api/v1/macro/events`
- Filing summary generation with template heuristics and prior-filing change detection.
- Worker extended with periodic filings and macro synchronization hooks.
- Dashboard macro panel now reads DB-backed macro events (provider fallback retained).
- Added Intel sync workspace (`/intel`) for manual filings/macro sync and visibility.

### Phase 7: Screener & Polish (Completed - MVP)

- Screener workspace (`/screener`) with richer filtering:
  - symbol query, asset type, sector, watchlist, tag
  - price, change %, market cap, volume ranges
  - sort + direction + limit controls
- Saved screens persistence and workflows:
  - list/create/update/delete/run saved screens
  - backend criteria parsing and re-run execution
- Keyboard interaction polish:
  - `/` focus symbol input
  - `Cmd/Ctrl+Enter` run screener
  - `Cmd/Ctrl+S` save current screen
- Loading/empty/error consistency pass:
  - global route loading skeleton
  - app-level error boundary (`app/error.tsx`)
  - shared `StateNotice` usage across major dashboard/workspace panels
- Phase 7 route and UI smoke coverage updates:
  - `test_screening_routes.py` for saved screen and extended filter APIs
  - frontend smoke coverage includes screener screen render

### Phase 8: Broker + Risk + Retrieval (Completed - MVP)

- Broker integration foundation (read-only):
  - broker provider abstraction (`BrokerProvider`) + mock broker adapter
  - broker sync persistence (`broker_accounts`, `broker_position_snapshots`, `broker_sync_runs`)
  - reconciliation endpoint against local portfolio holdings
- Portfolio risk snapshot:
  - `GET /api/v1/portfolio/risk`
  - concentration (HHI), top-position weights, factor bucket heuristics
  - scenario stress stubs with explicit assumptions and estimated impact
- Retrieval augmentation with citations:
  - `GET /api/v1/ai/research-qa`
  - retrieves from notes + filings corpus and returns ranked citation traces
- New UI surfaces:
  - `/broker` reconciliation workspace
  - portfolio risk panel in `/portfolio`
  - citation-backed QA panel in `/research`
- Added backend/frontend test coverage for Phase 8 flows.

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
