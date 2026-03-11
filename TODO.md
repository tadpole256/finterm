# TODO

## Phase 1 - Foundation

- [x] Monorepo structure and workspace scripts
- [x] Frontend/backend scaffolding with strict lint/type/test baselines
- [x] Baseline schema migration and deterministic seed pipeline
- [x] Worker scaffold and initial docs set

## Phase 2 - Core Market Workspace

- [x] Market provider abstraction + mock provider
- [x] Dashboard, watchlists, and security workspace APIs
- [x] Redis cache with in-memory fallback
- [x] Dashboard/watchlists/security frontend screens and charting
- [x] Phase 2 route and smoke test coverage

## Phase 3 - Research & Notes

- [x] Research note CRUD/search APIs and notebook workflows
- [x] Thesis model CRUD and synthesis layer
- [x] Note synthesis API alias in `/api/v1/ai`

## Phase 4 - Portfolio

- [x] Positions/transactions APIs with P&L and cost basis math
- [x] Portfolio workspace for holdings, transactions, and exposure views
- [x] Portfolio logic and route tests

## Phase 5 - Alerts & Briefs

- [x] Alert CRUD/evaluation, alert events, and notifications
- [x] Daily brief generate/latest flows
- [x] Worker scheduling hooks for alerts and briefs

## Phase 6 - Filings & Macro

- [x] Filings/macro provider adapters and sync endpoints
- [x] Filing summary and change-detection heuristics
- [x] Intel workspace visibility and worker sync hooks

## Phase 7 - Screener & Polish

- [x] Extended screener filters + saved screens lifecycle
- [x] Keyboard shortcuts and interaction polish
- [x] Empty/loading/error state pass across key workspaces

## Phase 8 - Broker + Risk + Retrieval

- [x] Broker sync/reconciliation MVP (read-first)
- [x] Portfolio risk snapshot API + UI panel
- [x] Citation-backed retrieval QA over notes + filings

## Phase 9 - Broker Execution Guardrails + Journal + Hybrid Retrieval

- [x] Broker capability/session endpoint with trading gate visibility
- [x] Order preview endpoint and mock provider support
- [x] Broker order event capture/listing endpoints and persistence
- [x] Reconciliation exception tracking and resolve flow
- [x] Trade journal domain + `/journal` UI workflow
- [x] Retrieval provider abstraction and hybrid citation scoring metadata
- [x] Phase 9 API and frontend smoke/integration coverage

## Validation

- [x] `npm run lint`
- [x] `npm run typecheck`
- [x] `npm run test`
- [ ] `npm run db:migrate && npm run db:seed` against running local PostgreSQL

## Next (Phase 10+)

- [ ] Broker auth/session lifecycle hardening (token refresh/reconnect/revoke)
- [ ] Optional order placement workflow with strict confirmations and kill-switches
- [ ] Enhanced reconciliation automation and exception classification
- [ ] Retrieval provider production adapter (managed embeddings/vector index)
