# TODO

## Phase 1 - Foundation

- [x] Create monorepo structure (`apps/web`, `apps/api`, `apps/worker`, `infra`, `docs`)
- [x] Configure root workspace scripts (`dev`, `lint`, `typecheck`, `test`, `db:migrate`, `db:seed`)
- [x] Set up Next.js + Tailwind + strict TypeScript frontend shell
- [x] Set up FastAPI + SQLAlchemy + Alembic backend shell
- [x] Add baseline Alembic migration covering required core entities
- [x] Add deterministic fixture set and seed pipeline
- [x] Add worker scaffold for scheduled jobs
- [x] Create core docs (`README.md`, `AGENTS.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `TODO.md`)

## Phase 2 - Core Market Workspace

- [x] Implement `MarketDataProvider` interface and mock provider
- [x] Implement dashboard API (`GET /api/v1/market/dashboard`)
- [x] Implement instrument search/detail APIs
- [x] Implement quote snapshot and historical bars APIs
- [x] Implement watchlist CRUD + item add/remove/reorder APIs
- [x] Implement security workspace API (`GET /api/v1/workspaces/security/{symbol}`)
- [x] Implement workspace layout persistence APIs
- [x] Implement Redis cache service with in-memory fallback
- [x] Build Dashboard screen
- [x] Build Watchlists screen
- [x] Build Security Workspace screen with charting and indicators
- [x] Add backend integration tests for key Phase 2 routes
- [x] Add frontend smoke tests for Dashboard, Watchlists, Security Workspace

## Validation

- [x] `npm run lint`
- [x] `npm run typecheck`
- [x] `npm run test`
- [ ] `npm run db:migrate && npm run db:seed` against a running local PostgreSQL service

## Phase 3 - Research & Notes

- [x] Research notebook CRUD/search APIs and UI workflows
- [x] Thesis aggregation + note synthesis service layer
- [x] AI note synthesis endpoint and prompt templates
- [x] Research-centric integration tests and UI smoke coverage

## Phase 4 - Portfolio

- [x] Portfolio APIs for positions/transactions with cost basis and P&L calculations
- [x] Portfolio UI view (`/portfolio`) for holdings, snapshots, exposures, and transactions
- [x] Link portfolio holdings to watchlists and research artifact counts
- [x] Portfolio math unit tests and route integration tests

## Phase 5 - Alerts & Briefs

- [x] Alert CRUD + evaluation APIs
- [x] Alert event history + notification listing/read APIs
- [x] Daily brief generation APIs (`latest`, `generate`)
- [x] Worker loop executes alert evaluation and once-per-day brief generation
- [x] Alerts workspace UI (`/alerts`) for alert management, events, notifications, and brief controls
- [x] Phase 5 backend and frontend test coverage

## Phase 6 - Filings & Macro

- [x] SEC-style filings adapter abstraction and mock provider fixture feed
- [x] Filing sync API + worker sync hook
- [x] Filing summary and change-detection heuristics on ingest
- [x] Macro series/event adapter abstraction and sync APIs
- [x] Dashboard macro panel switched to DB-backed events with provider fallback
- [x] Intel sync UI workspace (`/intel`) for filings/macro visibility + manual sync
- [x] Phase 6 backend/frontend test coverage

## Phase 7 - Screener & Polish

- [x] Saved screens UI workflows for screener persistence
- [x] Richer screening filters and result table ergonomics
- [x] Keyboard shortcuts and interaction polish
- [x] Loading/empty/error state consistency pass across major screens

## Phase 8 - Broker + Risk + Retrieval

- [x] Broker integration adapters and reconciliation model (read-only first)
- [x] Advanced portfolio risk snapshots (factor buckets, scenario stress stubs)
- [x] AI retrieval augmentation over filings + notes with citation traces

## Next (Phase 9+)

- [ ] Execution-ready broker adapters (auth/session lifecycle) behind strict capability flags
- [ ] Trade/order journal linkage to broker fills and reconciliation exceptions
- [ ] Semantic search/ranking upgrades for retrieval QA (embedding-backed, provider-pluggable)
