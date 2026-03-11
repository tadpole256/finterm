# AGENTS.md

Guidance for coding agents working in this repository.

## Mission

Build and evolve a personal market intelligence terminal with production-quality engineering discipline, while remaining legally cautious around market-data licensing.

## Core Standards

- Keep domain logic out of UI components.
- Keep provider-specific code behind provider interfaces.
- Prefer small, reviewable logical changes.
- Do not fake real-time data; always expose freshness/staleness.
- Preserve explicit source/provider metadata on market-derived records.

## Phase Guardrails

- Current implemented scope is Phase 1 through Phase 3.
- Do not silently add Phase 4+ product behavior unless explicitly requested.
- If extending scope, update `ROADMAP.md` and `TODO.md` in the same change.

## Data/Legal Guardrails

- Never assume data is redistributable.
- Treat entitlements as external configuration.
- Keep provider adapters swappable and explicit.
- Mark mock/delayed data clearly in API and UI.

## Repo Layout

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend, migrations, seed pipeline, tests
- `apps/worker`: background worker scaffold
- `infra`: environment and container orchestration assets
- `README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `TODO.md`: source-of-truth docs

## Commands

- Install JS deps: `npm install`
- Install API deps: `cd apps/api && python3 -m pip install -r requirements-dev.txt`
- Run app: `npm run dev`
- Lint: `npm run lint`
- Typecheck: `npm run typecheck`
- Tests: `npm run test`
- Migrate DB: `npm run db:migrate`
- Seed DB: `npm run db:seed`

## Testing Expectations

- Keep frontend smoke tests for primary screens current.
- Add/maintain backend integration tests for critical routes.
- Add targeted unit tests when logic complexity rises (indicators, filters, calculations).
- All PRs/changes should keep lint, typecheck, and tests passing.

## Non-goals

- Enterprise multi-tenant SaaS concerns.
- Fake Bloomberg visual clone.
- Over-engineered microservices for personal MVP scope.
- Price prediction claims disguised as AI features.
