# Roadmap

## Status Summary

- Phase 1: Completed
- Phase 2: Completed
- Phase 3: Completed (MVP)
- Phase 4: Completed (MVP)
- Phase 5: Completed (MVP)
- Phase 6: Completed (MVP)
- Phase 7: Completed (MVP)
- Phase 8: Completed (MVP)
- Phase 9: Completed (MVP)
- Phase 10+: Not started

## Phase Plan

### Phase 1: Foundation (Completed)

- Monorepo scaffold (`apps/web`, `apps/api`, `apps/worker`, `infra`)
- Tooling baseline (lint/typecheck/tests for web + API)
- Core schema/migrations + deterministic seed pipeline
- Base dark-theme application shell and required docs

### Phase 2: Core Market Workspace (Completed)

- Market data provider abstraction + mock implementation
- Dashboard APIs and UI shell
- Watchlist CRUD/reorder APIs and UI
- Security workspace API and chart indicators
- Redis cache + in-memory fallback

### Phase 3: Research & Notes (Completed - MVP)

- Research note CRUD/search APIs and notebook UI
- Thesis CRUD APIs and synthesis layer
- Note synthesis endpoints (`/research/synthesis`, `/ai/note-synthesis`)

### Phase 4: Portfolio (Completed - MVP)

- Portfolio overview/positions/transactions APIs
- Cost basis and realized/unrealized P&L calculations
- Portfolio workspace with exposure breakdown and transaction workflows

### Phase 5: Alerts & Briefs (Completed - MVP)

- Alert CRUD + evaluation APIs
- Alert events and notification read-state APIs
- Daily brief latest/generate APIs
- Worker hooks for scheduled evaluation and brief generation

### Phase 6: Filings & Macro (Completed - MVP)

- Filings and macro provider adapters with sync/list/detail routes
- Filing summary + change detection heuristics
- Worker sync hooks and Intel workspace visibility

### Phase 7: Screener & Polish (Completed - MVP)

- Expanded screener filters and saved screen lifecycle
- Keyboard shortcuts and denser interaction polish
- Improved empty/loading/error states across primary screens

### Phase 8: Broker + Risk + Retrieval (Completed - MVP)

- Broker read-only sync/reconciliation foundation
- Portfolio risk snapshot API and UI integration
- Citation-backed retrieval QA over notes + filings

### Phase 9: Broker Execution Guardrails + Journal + Hybrid Retrieval (Completed - MVP)

- Broker capability/session visibility endpoint:
  - `GET /api/v1/broker/capabilities`
- Execution-safe preview flow:
  - `POST /api/v1/broker/orders/preview`
  - controlled by `BROKER_TRADING_ENABLED` feature gate
- Broker order event lifecycle:
  - `POST /api/v1/broker/order-events`
  - `GET /api/v1/broker/order-events`
- Reconciliation exception lifecycle:
  - `GET /api/v1/broker/reconciliation-exceptions`
  - `PATCH /api/v1/broker/reconciliation-exceptions/{id}/resolve`
- Trade journal domain + UI:
  - `GET /api/v1/journal/entries`
  - `POST /api/v1/journal/entries`
  - `/journal` workspace for linked and standalone entries
- Hybrid retrieval scoring upgrades:
  - pluggable `RetrievalProvider` interface
  - deterministic `mock_embed` implementation
  - citation-level lexical/semantic/recency score details
- Data model additions:
  - `broker_order_events`
  - `reconciliation_exceptions`
  - `trade_journal_entries`

## Risks and Mitigations

- Data entitlements and redistribution ambiguity
  - Mitigation: adapter boundaries, explicit source metadata, mock-vs-live separation.
- Local service dependency drift (Postgres/Redis unavailable)
  - Mitigation: deterministic tests, in-memory cache fallback, runbook in README.
- Scope creep beyond personal workstation MVP
  - Mitigation: phase-gated backlog and explicit status updates in `TODO.md`.

## Data Provider Integration Strategy

1. Mock providers (current baseline)
2. Delayed/basic market data provider adapter
3. Premium entitlement-aware market and filings adapters
4. Broker adapters with session/auth lifecycle and stricter symbol/account mapping
5. Retrieval provider upgrades (vector index/managed embedding backend)

## Phase 10+ Candidate Backlog

- Broker auth/session lifecycle hardening (refresh/revoke/persistence)
- Optional order placement workflow with strict safety/confirmation policies
- Reconciliation auto-remediation suggestions and richer exception taxonomy
- Advanced alert routing/escalation policies
- Deeper macro calendar and earnings/event adapters
