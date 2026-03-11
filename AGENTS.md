# AGENTS.md

Guidance for coding agents working in this repository.

## Mission

Build and evolve a serious personal market intelligence terminal with production-quality discipline and explicit legal/data caution around provider entitlements.

## Current Scope Guardrail

- Implemented scope is Phase 1 through Phase 9 (MVP).
- Do not silently add Phase 10+ behavior without an explicit user request.
- When scope changes, update `README.md`, `ROADMAP.md`, and `TODO.md` in the same change set.

## Engineering Standards

- Keep UI rendering separate from domain and provider logic.
- Keep provider-specific integration behind interfaces (`MarketDataProvider`, `BrokerProvider`, `RetrievalProvider`, filings/macro adapters).
- Preserve freshness/source metadata in market-facing responses.
- Never imply real-time if feed is delayed or mocked.
- Prefer small, reviewable, test-backed changes over broad rewrites.

## Legal/Data Guardrails

- Never assume redistribution rights for market data.
- Keep entitlements/config externalized to env and adapter settings.
- Keep mock, delayed, and premium/personal-broker adapters clearly separated.
- Surface degraded/stale data honestly in API and UI.

## Repo Layout

- `apps/web`: Next.js frontend (App Router, Tailwind, Vitest smoke tests)
- `apps/api`: FastAPI backend (SQLAlchemy, Alembic, pytest, ruff, mypy)
- `apps/worker`: background polling/scheduler loop
- `infra`: local infra templates and future deployment placeholders
- Root docs: `README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `TODO.md`

## Commands

- Install JS deps: `npm install`
- Install API deps: `cd apps/api && python3 -m pip install -r requirements-dev.txt`
- Run app: `npm run dev`
- Run worker: `npm run dev:worker`
- Lint: `npm run lint`
- Typecheck: `npm run typecheck`
- Test: `npm run test`
- DB migrate: `npm run db:migrate`
- DB seed: `npm run db:seed`

## Testing Expectations

- Keep smoke coverage for all primary workspaces (`/`, `/watchlists`, `/security/[symbol]`, `/portfolio`, `/alerts`, `/research`, `/screener`, `/broker`, `/journal`).
- Keep integration tests for critical route families and high-risk service logic.
- Maintain deterministic fixtures for provider-backed flows and indicator/ranking logic.
- Merge-ready changes must pass `npm run lint`, `npm run typecheck`, `npm run test`.

## Non-Goals

- Multi-tenant enterprise SaaS complexity.
- UI mimicry of Bloomberg branding/look-and-feel.
- Hidden coupling of broker execution logic into market data adapters.
- AI claims of guaranteed market prediction.
