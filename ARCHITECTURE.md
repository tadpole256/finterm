# Architecture

## System Shape

Finterm is a modular monorepo for one advanced user, deployed locally as a single stack:

- Web: Next.js App Router (`apps/web`)
- API: FastAPI + SQLAlchemy + Alembic (`apps/api`)
- Worker: Python polling loop (`apps/worker`)
- Durable store: PostgreSQL
- Cache/coordination: Redis with in-process fallback

The architecture favors clear domain boundaries and provider adapters over early microservice complexity.

## Domain Modules

### 1) Market Data Domain

Responsibilities:
- instrument search/detail
- quote snapshots and historical bars
- dashboard aggregate, movers, and freshness signaling
- chart indicator inputs

Key modules:
- `app/services/market_provider.py`
- `app/services/market.py`
- `app/services/cache.py`
- routes: `app/api/routes/market.py`, `app/api/routes/instruments.py`, `app/api/routes/prices.py`

### 2) Workspace + Watchlist Domain

Responsibilities:
- watchlist CRUD, symbol membership, reordering
- workspace layout persistence per page
- security workspace aggregate payload

Key modules:
- `app/services/watchlists.py`
- `app/services/workspace.py`
- routes: `app/api/routes/watchlists.py`, `app/api/routes/workspaces.py`

### 3) Research + AI Domain

Responsibilities:
- research notes, tags, theses, catalysts
- note synthesis and daily/periodic knowledge views
- citation-backed Q&A over notes/filings corpus
- hybrid ranking (lexical + semantic + recency)

Key modules:
- `app/services/research.py`
- `app/services/research_qa.py`
- `app/services/retrieval_provider.py`
- routes: `app/api/routes/research.py`, `app/api/routes/ai.py`

### 4) Portfolio + Risk Domain

Responsibilities:
- transactions, position rollups, cost basis/P&L
- exposure and risk snapshots (concentration/factor/scenario stubs)
- linkage to research/watchlists and broker reconciliation

Key modules:
- `app/services/portfolio.py`
- `app/services/risk.py`
- routes: `app/api/routes/portfolio.py`

### 5) Alerts + Briefs Domain

Responsibilities:
- alert definitions and evaluation
- notification history/read state
- daily brief generation and retrieval

Key modules:
- `app/services/alerts.py`
- `app/services/briefs.py`
- routes: `app/api/routes/alerts.py`, `app/api/routes/notifications.py`, `app/api/routes/briefs.py`
- worker hooks in `apps/worker/main.py`

### 6) Filings + Macro Domain

Responsibilities:
- filings and macro ingestion through adapters
- filing summary/change detection heuristics
- dashboard/security context integration

Key modules:
- `app/services/filings_provider.py`
- `app/services/filings.py`
- `app/services/macro_provider.py`
- `app/services/macro.py`
- routes: `app/api/routes/filings.py`, `app/api/routes/macro.py`

### 7) Broker + Journal Domain

Responsibilities:
- broker account sync snapshots
- reconciliation vs local portfolio
- reconciliation exception lifecycle (open/resolved)
- order preview + order-event capture (capability-gated)
- trade journal linkage to transactions/order events

Key modules:
- `app/services/broker_provider.py`
- `app/services/broker.py`
- `app/services/journal.py`
- routes: `app/api/routes/broker.py`, `app/api/routes/journal.py`

## Data Model and Separation

Durable research/portfolio state is stored separately from transient market data snapshots:

- Durable research and planning: `research_notes`, `theses`, `catalyst_events`, `trade_journal_entries`
- Durable portfolio/accounting: `portfolios`, `positions`, `transactions`
- External sync snapshots/audit: `quote_snapshots`, `historical_bars`, `broker_*`, `filings`, `macro_*`
- Operational outputs: `alerts`, `alert_events`, `notifications`, `daily_briefs`, `workspace_layouts`

Phase 9 additions:
- `broker_order_events`
- `reconciliation_exceptions`
- `trade_journal_entries`

## Data Flow

1. UI calls `/api/v1/...`.
2. Route layer resolves user context and provider configuration from env-backed dependencies.
3. Domain service orchestrates DB access, provider calls, cache, and derived logic.
4. Response payload includes provider/freshness metadata where applicable.
5. UI renders data with explicit stale/degraded indicators and does not simulate live feeds.

## Provider Abstraction Model

Provider adapters are selected through config and kept independent:

- `MARKET_DATA_PROVIDER=alpha_vantage|mock|delayed|premium`
- `ALPHA_VANTAGE_API_KEY` (required when `MARKET_DATA_PROVIDER=alpha_vantage`)
- `ALPHA_VANTAGE_BASE_URL` (defaults to `https://www.alphavantage.co/query`)
- `FILINGS_PROVIDER=mock_sec|...`
- `MACRO_PROVIDER=mock_macro|...`
- `BROKER_PROVIDER=mock_broker|...`
- `RETRIEVAL_PROVIDER=mock_embed|...`

Safety gate:
- `BROKER_TRADING_ENABLED=false` by default. Execution-adjacent endpoints remain preview/simulation-focused unless explicitly enabled.

## Caching Model

Redis cache keys are namespaced by provider and request shape (for example dashboard and bar series keys).  
If Redis is unavailable, API falls back to in-process cache and marks degraded freshness semantics in response metadata.

## Ingestion and Scheduling Model

- Seed pipeline (`app/seed.py`) provides deterministic local datasets for all implemented domains.
- Worker loop (`apps/worker`) runs periodic alert/brief/filings/macro jobs and is intentionally lightweight for local operation.
- The scheduler can be replaced later without changing domain service contracts.

## Extensibility Notes

- Keep broker execution and reconciliation concerns isolated from market data adapters.
- Preserve deterministic mock fixtures to keep CI and local testing stable.
- Evolve retrieval provider from mock embeddings to a managed/vector backend without changing API contracts.
- Add entitlement-aware metadata before integrating premium market feeds or broker trade placement.
