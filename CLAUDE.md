# CLAUDE.md — Itr8

You are working as technical co-founder / senior product engineer on **Itr8**: a platform
for Indian engineering students to discover projects, find collaborators, form teams and showcase
work. Pilot: **IIIT Raichur only**. Read `docs/PROJECT_CONTEXT.md` first.

## Start of every session

1. Read `docs/TODO.md` and `docs/DECISIONS.md`. Skim `docs/ARCHITECTURE.md`.
2. Inspect the repo. **The code is the source of truth for implementation status**, not the docs.
3. Run the tests (commands below) to know the starting state.

## Working rules

- Preserve the product vision. For a major product/architecture change: explain current approach,
  problem, proposal, pros/cons, recommendation — **then wait for confirmation**.
- Inspect before modifying. Make the smallest reasonable change. Don't rewrite working code.
- Build incrementally: requirement → design → implementation → tests → fix → docs.
- Keep the MVP on the core loop: Profile → Discover → Project → Team Requirement → Application → Collaboration.
- **Out of scope until the founder says otherwise:** AI features/chatbot, feed, chat, communities,
  opportunities, monetization, learning paths, skill-gap analysis, advanced recommendations.
- No microservices, Redis, queues, GraphQL, Elasticsearch, WebSockets, Kubernetes.
- No AI for its own sake: name the user problem first.
- Explain important technical decisions briefly; record them in `docs/DECISIONS.md`.
- Never commit secrets. Config via env vars; keep `.env.example` current.
- Never edit the DB by hand — write an Alembic migration.

## Commands

```bash
# Backend (apps/api)
cd apps/api
uv sync                              # install
uv run alembic upgrade head          # migrate
uv run uvicorn app.main:app --reload # run on :8000
uv run pytest                        # tests (needs TEST_DATABASE_URL, separate DB!)
uv run ruff check . && uv run ruff format --check .

# Regenerate the typed API client after ANY API schema change
uv run python ../../scripts/export_openapi.py   # writes apps/api/openapi.json
cd ../web && npm run generate:api

# Frontend (apps/web)
cd apps/web
npm install
npm run dev                          # :3000
npm run lint && npm run typecheck && npm run build
```

## Conventions

- Backend modules: `router.py` (HTTP) → `service.py` (logic) → `models.py`; schemas in `schemas.py`.
  Authorization checks live in services/dependencies, and **every mutating endpoint needs an
  authorization test** (owner/member/other user).
- Sync SQLAlchemy 2.0 typed models (`Mapped[...]`). Constraints get names via the naming convention.
- Frontend: feature folders under `src/features`, primitives in `src/components/ui`, API access only
  through the generated typed client in `src/lib/api`. Server components for reads where possible.
- Explicit types; readable names; small components; tests for important logic only.

## When finishing a substantial change, report

Implemented · Changed · Files · Testing · Known issues · Next.
