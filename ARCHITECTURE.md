# Architecture

## System Shape

Finterm is a modular monorepo with service boundaries by domain, deployed as a single local stack for personal use.

- **Web**: Next.js App Router (`apps/web`)
- **API**: FastAPI service (`apps/api`)
- **Worker**: Python background loop scaffold (`apps/worker`)
- **Persistence**: PostgreSQL
- **Cache/coordination**: Redis (with in-process fallback)

## Domain Modules

### 1) Market Data Domain

Responsibilities:
- market snapshot
- quote snapshots
- historical bars
- movers
- instrument search/detail
- freshness signaling

Implemented modules:
- `app/services/market_provider.py`
- `app/services/market.py`
- `app/services/cache.py`
- routes in `app/api/routes/market.py`

### 2) Research Domain

Implemented behaviors:
- `research_notes`, `research_tags`, `research_note_tags`, `theses`, `catalyst_events`
- research note CRUD + search (`/research/notes`)
- thesis CRUD (`/research/theses`)
- research theme lookup (`/research/themes`)
- research notebook UI at `/research`
- security workspace continues to surface recent notes/catalysts for symbol context

### 3) Portfolio Domain

Schema implemented for future phases:
- `portfolios`, `positions`, `transactions`

No full portfolio UI/API behavior in Phase 1–2 by design.

### 4) Alerts Domain

Schema + dashboard surfacing:
- `alerts`, `alert_events`, `notifications`
- active alerts shown on dashboard from seeded rules

### 5) Filings & Macro Domain

Implemented baseline:
- `filings`, `filing_summaries`, `macro_series`, `macro_events`
- security workspace shows recent filings
- dashboard shows macro events

### 6) AI Assist Domain

Implemented behaviors:
- seeded daily brief content (`daily_briefs`)
- seeded “what changed” narrative in security workspace
- note synthesis endpoint (`/research/synthesis`) and alias (`/ai/note-synthesis`)
- heuristic synthesis service deriving:
  - synthesized thesis
  - open questions
  - risks
  - next items to watch

## Data Flow

1. UI calls `/api/v1/...` endpoints.
2. API domain service resolves request:
   - reads/writes durable state in PostgreSQL
   - requests market payloads from provider adapter
   - applies caching for dashboard and bars
3. API returns normalized response envelope with:
   - `source_provider`
   - `as_of`
   - `delay_seconds`
   - `freshness_status`
   - `is_stale`
4. UI renders stale/degraded state explicitly.

## Caching Model

- Redis cache keys are namespaced by provider and query params:
  - `finterm:{provider}:dashboard:{user_id}`
  - `finterm:{provider}:bars:{symbol}:{timeframe}`
- If Redis is unavailable, service falls back to in-memory cache and marks degraded freshness semantics.

## Ingestion/Seed Model

- Deterministic fixture-backed provider data (`app/fixtures/*.json`)
- `app/seed.py` seeds DB with:
  - instruments
  - watchlists + items
  - quote snapshots
  - historical bars
  - macro events
  - alerts
  - filings + filing summaries
  - research notes + catalysts
  - daily brief
  - workspace layout

## Provider Abstraction

`MarketDataProvider` protocol defines swappable data backends.

Current implementation:
- `MockMarketDataProvider`

Configured by env:
- `MARKET_DATA_PROVIDER=mock|delayed|premium`
- non-mock names currently route to same mock backend for MVP compatibility

This keeps API/services stable while live providers are integrated later.

## Future Extensibility Notes

- Add broker adapter boundary separately from market data provider.
- Move worker from loop scaffold to scheduled job framework when Phase 5 starts.
- Introduce dedicated AI service interface for summarization/change detection workflows.
- Add provider entitlement checks and per-feed delay/rights metadata before live feed enablement.
