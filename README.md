# Finterm

Finterm is a personal market intelligence terminal for one advanced user. It focuses on high-signal monitoring, research context, charting, and workflow speed without pretending to be an enterprise Bloomberg replacement.

## Product Vision

- Personal command center for market monitoring and research execution.
- Modular architecture that can evolve from seeded/mock data to licensed providers.
- AI used for summarization and triage, not deterministic prediction claims.
- Honest UI signals for stale/delayed/degraded data.

## Current Scope (Implemented: Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5 MVP)

- Foundation monorepo (`Next.js` frontend, `FastAPI` backend, worker scaffold).
- Full baseline schema + Alembic migration for required core entities.
- Mock provider abstraction with deterministic fixture-backed data.
- Dashboard (`/`) with market snapshot, watchlists, movers, macro events, active alerts, morning brief.
- Watchlists workspace (`/watchlists`) with create/add/remove/reorder and persisted layout state.
- Security workspace (`/security/[symbol]`) with key stats, chart, overlays (SMA/EMA/RSI/MACD), filings/notes/catalyst context.
- Research notebook (`/research`) with note create/edit/delete/search, thesis tracking, and note synthesis.
- Portfolio workspace (`/portfolio`) with holdings, transactions, P&L summary, sector exposure, and links to research/watchlists.
- Alerts workspace (`/alerts`) with alert CRUD, manual evaluation, event history, notification read-state, and daily brief controls.
- API routes for market, watchlists, bars, instrument search/detail, workspace security payload, layout persistence, basic screening, and research.
- Portfolio APIs for overview, positions, transaction history, create transaction, and delete transaction.
- Alerts + notifications + brief APIs with worker execution loop for scheduled evaluations/generation.
- Redis cache service with in-memory fallback and degraded freshness signaling.

## Architecture Overview

- **Frontend (`apps/web`)**: Next.js App Router + TypeScript + Tailwind, dark-first workstation layout.
- **API (`apps/api`)**: FastAPI, SQLAlchemy ORM, Alembic migrations, domain services.
- **Worker (`apps/worker`)**: background loop scaffold for scheduled jobs (alerts/brief generation hooks).
- **Data**: PostgreSQL for durable domain state; Redis for cache/coordination with graceful fallback.
- **Providers**: `MarketDataProvider` interface with `MockMarketDataProvider` implemented (`MARKET_DATA_PROVIDER=mock|delayed|premium`, currently mock-backed).

Detailed design: see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Legal and Data Guardrails

- No illegal redistribution of licensed market data is implemented or implied.
- Provider entitlements and redistribution rights are external dependencies.
- Mock data is clearly separated from live entitlements.
- UI includes stale/degraded markers rather than faking real-time.

## Local Setup (macOS/Homebrew)

1. Install services:

```bash
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
```

2. Create database:

```bash
createdb finterm
```

3. Install dependencies:

```bash
npm install
cd apps/api && python3 -m pip install -r requirements-dev.txt && cd ../..
```

4. Configure environment:

```bash
cp .env.example .env
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env.local
```

5. Apply migration and seed:

```bash
npm run db:migrate
npm run db:seed
```

6. Start app:

```bash
npm run dev
```

Optional worker loop:

```bash
npm run dev:worker
```

- Web: `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

## Development Workflow

- Lint: `npm run lint`
- Typecheck: `npm run typecheck`
- Tests: `npm run test`
- DB migrate: `npm run db:migrate`
- DB seed: `npm run db:seed`

## Key Implemented API Endpoints

- `GET /api/v1/market/dashboard`
- `GET /api/v1/instruments/search`
- `GET /api/v1/instruments/{symbol}`
- `GET /api/v1/quotes/snapshots`
- `GET /api/v1/prices/bars/{symbol}`
- `GET|POST|PATCH|DELETE /api/v1/watchlists...`
- `GET /api/v1/workspaces/security/{symbol}`
- `GET|PUT /api/v1/workspaces/layout/{workspace}`
- `GET /api/v1/screening/run`
- `GET|POST|PATCH|DELETE /api/v1/research/notes...`
- `GET|POST|PATCH|DELETE /api/v1/research/theses...`
- `GET /api/v1/research/themes`
- `GET /api/v1/research/synthesis`
- `GET /api/v1/ai/note-synthesis`
- `GET /api/v1/portfolio/overview`
- `GET /api/v1/portfolio/positions`
- `GET /api/v1/portfolio/transactions`
- `POST /api/v1/portfolio/transactions`
- `DELETE /api/v1/portfolio/transactions/{transaction_id}`
- `GET|POST|PATCH|DELETE /api/v1/alerts...`
- `GET /api/v1/alerts/events`
- `POST /api/v1/alerts/evaluate`
- `GET /api/v1/notifications`
- `PATCH /api/v1/notifications/{notification_id}/read`
- `GET /api/v1/briefs/latest`
- `POST /api/v1/briefs/generate`

## Roadmap

See [ROADMAP.md](./ROADMAP.md) and execution checklist in [TODO.md](./TODO.md).
